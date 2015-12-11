"""
Tests for manager module.
"""
import pytest
import mock
import tower
import time
mockTower = mock.MagicMock()

def test_init(tmpdir):
    manager = tower.WorkflowManager(test_directory=str(tmpdir))

def test_start(tmpdir):
    manager = tower.WorkflowManager(test_directory=str(tmpdir))
    manager.add_tower(mockTower)
    manager.start()

def test_teardown(tmpdir):
    manager = tower.WorkflowManager(test_directory=str(tmpdir))
    manager.add_tower(mockTower)
    manager.start()
    time.sleep(.005)
    manager.end()
