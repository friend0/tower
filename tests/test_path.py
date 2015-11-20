import logging

import mock
import pytest

import tower.mapping.path as path

logging.basicConfig(level=logging.DEBUG)

mockPoint = mock.MagicMock()


def test_node_init():
    """
    Test that Node class' init function produces an object given some point as data.
    Test that it can store a reference to previous and next object
    :return:
    """
    assert isinstance(path.Node(mockPoint), object)


def test_node_connect():
    """
    Test Node next and previous properties
    :return:
    """
    point_a = path.Node(mockPoint)
    point_b = path.Node(mockPoint)
    point_a.next = point_b
    point_b.prev = point_a
    assert (point_a.prev is None)
    assert (point_b.next is None)
    assert (point_a.next is point_b)
    assert (point_b.prev is point_a)


def test_edge_exception():
    """
    Check that edge raises an exception if we try to make an edge between a node and itself
    :return:
    """
    point_a = path.Node(mockPoint)
    with pytest.raises(Exception):
        isinstance(path.Edge(point_a, point_a), object)


def test_edge():
    """
    Check that Edge gets instantiated correctly, that we can access constituent nodes, and that they have been connected
    :return:
    """
    point_a = path.Node(mockPoint)
    point_b = path.Node(mockPoint)
    edge = path.Edge(point_a, point_b)
    assert (isinstance(edge, path.Edge))
    assert (edge.start.next is edge.end)
    assert (edge.end.prev is edge.start)
    assert (edge.start.prev is None)
    assert (edge.end.prev is edge.start)


def test_path():
    """
    Check that Edge gets instantiated correctly, that we can access constituent nodes, and that they have been connected
    :return:
    """
    point_a = path.Node(mockPoint)
    point_b = path.Node(mockPoint)
    point_c = path.Node(mockPoint)
    edge_ab = path.Edge(point_a, point_b)
    edge_bc = path.Edge(point_b, point_c)

    trajectory = path.Path([edge_ab, edge_bc])
    assert (trajectory.has_next())
    while trajectory.has_next():
        assert (isinstance(trajectory.next(), object))
    assert (not trajectory.has_next())
    with pytest.raises(StopIteration):
        isinstance(trajectory.next(), object)
