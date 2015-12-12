import logging

import mock

import tower.map.graph as graph

logging.basicConfig(level=logging.DEBUG)
mockVertex = mock.MagicMock()

G = {'a': {'b': 10},
     'b': {'c': 1, 'x': 2},
     'c': {'y': 4}
     }


def test_node_init():
    """

    Test that Node class' init function produces an object given some point as data.
    Test that it can store a reference to previous and next object
    :return:

    """
    g = graph.Graph(G)
    assert isinstance(g, object)


def test_implicit_graph_creation():
    """

    Test that a graph can be made from a dictionary definition of nodes, neighbors and weights
    :return:

    """
    g = graph.Graph(G)
    assert (g.num_vertices == 5)


def test_add_vertex():
    """

    Test that a graph can be made from a dictionary definition of nodes, neighbors and weights
    :return:

    """
    g = graph.Graph(G)
    g.add_vertex(mockVertex)
    assert (g.num_vertices == 6)


def test_remove_vertex():
    """

    Test that a graph can be made from a dictionary definition of nodes, neighbors and weights
    :return:

    """
    g = graph.Graph(G)
    g.remove_vertex(mockVertex)
    assert (g.num_vertices == 4)


def test_edges():
    """

    Test that a graph can be made from a dictionary definition of nodes, neighbors and weights
    :return:

    """
    g = graph.Graph(G)
    assert (len(g.get_edges()) == 4)


def test_shortest_path():
    """

    Use dijkstra's algorithm to find the shortest path
    :return:

    """
    g = graph.Graph(G)

    assert (g.shortest_path('a', 'b') == [u'a', u'b'])
    assert (g.shortest_path('a', 'c') == [u'a', u'b', u'c'])


'''



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

'''
