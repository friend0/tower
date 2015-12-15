"""

Tests for manager module.

"""

import mock


import tower
import time

mockTower = mock.MagicMock()


def test_init(tmpdir):
    """

    Test instantiation of a WorkflowManager object
    :param tmpdir: temp directory provided  by test framework

    """
    manager = tower.WorkflowManager(log_directory=str(tmpdir))
    manager.end()


def test_start(tmpdir):
    """

    Test that the WorkflowManager starts correctly
    :param tmpdir: temp directory provided  by test framework

    """

    manager = tower.WorkflowManager(log_directory=str(tmpdir))
    manager.add_tower(mockTower)
    manager.end()


def test_teardown(tmpdir):
    """

    Test setup and teardown of WorkflowManager, make sure that all threads and processes have been shut down correctly
    :param tmpdir:

    """
    manager = tower.WorkflowManager(log_directory=str(tmpdir))
    manager.add_tower(mockTower)
    time.sleep(.005)
    manager.end()
    # todo: make sure the processes have cleaned themselves up
