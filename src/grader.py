#!/usr/bin/env python3
import unittest
import random
import sys
import copy
import argparse
import inspect
import collections
import os
import pickle
import gzip
from graderUtil import graded, CourseTestRunner, GradedTestCase
import numpy as np
import torch
import torch.nn as nn
import omniglot
from google_drive_downloader import GoogleDriveDownloader as gdd
import torch.nn.functional as F  # pylint: disable=unused-import

# Import submission
import submission
import util  # pylint: disable=unused-import

#############################################
# HELPER FUNCTIONS FOR CREATING TEST INPUTS #
#############################################

def fix_random_seeds(
        seed=123,
        set_system=True,
        set_torch=False):
    """
    Fix random seeds for reproducibility.
    Parameters
    ----------
    seed : int
        Random seed to be set.
    set_system : bool
        Whether to set `np.random.seed(seed)` and `random.seed(seed)`
    set_torch : bool
        Whether to set `torch.manual_seed(seed)`
    """
    # set system seed
    if set_system:
        random.seed(seed)
        np.random.seed(seed)

    # set torch seed
    if set_torch:
        torch.manual_seed(seed)

def check_omniglot():
    """
    Check if Omniglot dataset is available.
    """
    if not os.path.isdir("./omniglot_resized"):
        gdd.download_file_from_google_drive(
            file_id="1iaSFXIYC3AB8q9K_M-oVMa4pmB7yKMtI",
            dest_path="./omniglot_resized.zip",
            unzip=True,
        )
    assert os.path.isdir("./omniglot_resized"), "Omniglot dataset is not available! Run `python maml.py --cache` first to download the dataset!"

#########
# TESTS #
#########

# Baseline
class Test_1b(GradedTestCase):
    def setUp(self):
        # self.dataloader_train = _dataloader_helper()
        check_omniglot()
        self.dataloader_train = omniglot.get_omniglot_dataloader(
            split='train',
            batch_size=16,
            num_way=5,
            num_support=1,
            num_query=15,
            num_tasks_per_epoch=240000,
            num_workers=1,
        )
        self.log_dir = "tests"
        self.learning_rate = 0.001

    ### BEGIN_HIDE ###
    ### END_HIDE ###

class Test_2a(GradedTestCase):
    def setUp(self):
        check_omniglot()
        self.dataloader_train = omniglot.get_omniglot_dataloader(
            split='train',
            batch_size=16,
            num_way=5,
            num_support=1,
            num_query=15,
            num_tasks_per_epoch=240000,
            num_workers=1,
        )

        self.parameters_keys = ['conv0', 'b0', 'conv1', 'b1', 'conv2', 'b2', 'conv3', 'b3', 'w4', 'b4']
        self.submission_maml = submission.MAML(
            num_outputs=5,
            num_inner_steps=1,
            inner_lr=0.4,
            learn_inner_lrs=False,
            outer_lr=0.001,
            log_dir='./logs/'
        )
        self.solution_maml = self.run_with_solution_if_possible(submission, lambda sub_or_sol:sub_or_sol.MAML(
            num_outputs=5,
            num_inner_steps=1,
            inner_lr=0.4,
            learn_inner_lrs=False,
            outer_lr=0.001,
            log_dir='./logs/'
        ))

    @graded(timeout=60)
    def test_0(self):
        """2a-0-basic: check prediction and accuracies shape for _inner_loop"""
        fix_random_seeds()
        for i_step, task_batch in enumerate(
                self.dataloader_train,
                start=0
        ):
            for task in task_batch:
                images_support, labels_support, images_query, labels_query = task
                images_support = images_support
                labels_support = labels_support
                images_query = images_query
                labels_query = labels_query
                parameters, accuracies = self.submission_maml._inner_loop(
                    images_support,
                    labels_support,
                    True
                )
                self.assertTrue(parameters['conv0'].shape == torch.Size([64, 1, 3, 3]), "conv0 shape is incorrect")
                self.assertTrue(parameters['b0'].shape == torch.Size([64]), "b0 shape is incorrect")
                self.assertTrue(parameters['conv1'].shape == torch.Size([64, 64, 3, 3]), "conv1 shape is incorrect")
                self.assertTrue(parameters['b1'].shape == torch.Size([64]), "b1 shape is incorrect")
                self.assertTrue(parameters['conv2'].shape == torch.Size([64, 64, 3, 3]), "conv2 shape is incorrect")
                self.assertTrue(parameters['b2'].shape == torch.Size([64]), "b2 shape is incorrect")
                self.assertTrue(parameters['conv3'].shape == torch.Size([64, 64, 3, 3]), "conv3 shape is incorrect")
                self.assertTrue(parameters['b3'].shape == torch.Size([64]), "b3 shape is incorrect")
                self.assertTrue(parameters['w4'].shape == torch.Size([5, 64]), "w4 shape is incorrect")
                self.assertTrue(parameters['b4'].shape == torch.Size([5]), "b4 shape is incorrect")
                self.assertTrue(len(accuracies) == 2, "accuracies length is incorrect")
                break
            break
    
    ### BEGIN_HIDE ###
    ### END_HIDE ###

class Test_2b(GradedTestCase):
    def setUp(self):
        check_omniglot()
        self.dataloader_train = omniglot.get_omniglot_dataloader(
            split='train',
            batch_size=8,
            num_way=5,
            num_support=1,
            num_query=15,
            num_tasks_per_epoch=240000,
            num_workers=1,
        )
        self.parameters_keys = ['conv0', 'b0', 'conv1', 'b1', 'conv2', 'b2', 'conv3', 'b3', 'w4', 'b4']
        self.submission_maml = submission.MAML(
            num_outputs=5,
            num_inner_steps=1,
            inner_lr=0.4,
            learn_inner_lrs=False,
            outer_lr=0.001,
            log_dir='./logs/'
        )
        self.solution_maml = self.run_with_solution_if_possible(submission, lambda sub_or_sol:sub_or_sol.MAML(
            num_outputs=5,
            num_inner_steps=1,
            inner_lr=0.4,
            learn_inner_lrs=False,
            outer_lr=0.001,
            log_dir='./logs/'
        ))
    
    @graded(timeout=60)
    def test_0(self):
        """2b-0-basic: check shapes are correct for _outer_step"""
        fix_random_seeds()
        for i_step, task_batch in enumerate(
                self.dataloader_train,
                start=0
        ):
            self.submission_maml._optimizer.zero_grad()
            outer_loss, accuracies_support, accuracy_query = (
                self.submission_maml._outer_step(task_batch, train=True)
            )
            self.assertTrue(outer_loss.shape == torch.Size([]))
            self.assertTrue(accuracies_support.shape == (2,))
            self.assertTrue(type(accuracy_query) == np.float64)
            break
    
    ### BEGIN_HIDE ###
    ### END_HIDE ###

def getTestCaseForTestID(test_id):
    question, part, _ = test_id.split("-")
    g = globals().copy()
    for name, obj in g.items():
        if inspect.isclass(obj) and name == ("Test_" + question):
            return obj("test_" + part)

if __name__ == "__main__":
    # Parse for a specific test
    parser = argparse.ArgumentParser()
    parser.add_argument("test_case", nargs="?", default="all")
    test_id = parser.parse_args().test_case

    assignment = unittest.TestSuite()
    if test_id != "all":
        assignment.addTest(getTestCaseForTestID(test_id))
    else:
        assignment.addTests(
            unittest.defaultTestLoader.discover(".", pattern="grader.py")
        )
    CourseTestRunner().run(assignment)
