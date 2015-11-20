from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tower.utils.utils import grouper


class Node(object):
    """

    Node stores a point, and serves as a Vertex in a graph object, or in our case, the specification of a path.
    Most commonly, Node will be used to wrap a Point object from the region Module.

    """
    def __init__(self, point, prev=None, next=None):
        self.data = point  # data is a named tuple describing an atomic point
        self.prev = prev  # prev is a reference to the coordinate before
        self.next = next  # reference to the next coordinate

    def __str__(self):
        return str(self.data)


class Edge(object):
    """

    Edge describes the connection between two nodes, with direction. Also has weight.

    """

    def __init__(self, node_a, node_b):
        self.weight = None
        if node_a is not node_b:
            self.start = node_a  # data is a named tuple of type coordinate
            self.end = node_b  # prev is a reference to the coordinate before
        else:
            raise Exception("Cannot create an edge from a point to itself")
        self.start.next = self.end
        self.end.prev = self.start

    def connect_forward(self, edge):
        self.end.next = edge.start.prev

    def connect_reverse(self, edge):
        self.start.prev = edge.end.next


class Path(object):
    """

    Formally, can be understood to represent a simply connected, directed graph.
    Given a set of

    """

    def __init__(self, edges):

        self.edges = edges
        self.idx = -1
        for edge1, edge2 in grouper(self.edges, 2):
            edge1.connect_forward(edge2)
            edge2.connect_reverse(edge1)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """

        Get the next Coord in path

        """
        if self.idx < len(self.edges) - 1:
            self.idx += 1
            return self.edges[self.idx]
        else:
            self.idx = len(self.edges)
            raise StopIteration

    def has_next(self):
        """

        Return true if there are more nodes after current node in dll

        """
        if self.idx < len(self.edges)-1:
            return True
        else:
            return False

    def previous(self):
        """

        Get the previous coordinate in path

        """

        pass

    def has_previous(self):
        """

        Return true if there are nodes before current node in dll

        """
        if self.idx < len(self.nodes):
            return True
        else:
            return False

    def insert(self):
        pass

    def remove(self):
        pass


class Cycle(Path):
    """

    Cycle is a connected path that can be traversed continuously

    """
    pass



'''
class Coord(object):
    def __init__(self, data, prev, next):
        self.data = data  # data is a named tuple of type coordinate
        self.prev = prev  # prev is a reference to the coordinate before
        self.next = next  # reference to the next coordinate

    def __str__(self):
        return str(self.data)


class Path(object):
    """

    The path class holds a dictionary of coordinates representing a path, and also stores corresponding information on:
    elevation, distance from last point, lat distance to next point, lon distance to next point,

    """

    def __init__(self, path_info, mode='circular'):

        self.path_info = path_info
        self.coordinates = self.path_info['coords']
        # dll of nodes, where node is a wrapper object 'Coord' for named tuple Coordinates
        self.nodes = [Coord(item, self.coordinates[idx - 1] if idx >= 1 else None,
                            self.coordinates[idx + 1] if idx < len(self.coordinates) - 1 else None) for idx, item in
                      enumerate(self.coordinates)]
        self.elevation = grouper(self.coordinates, 2)
        self.distance = grouper(self.path_info['distance'], 2)
        self.lat_distance = grouper(self.path_info['latDistance'], 2)
        self.lon_distance = grouper(self.path_info['lonDistance'], 2)
        self.idx = -1
        self.mode = mode

    def __iter__(self):
        return self

    def __next__(self):
        """

        Get the next Coord in path

        """
        if self.idx < len(self.nodes) - 1:
            self.idx += 1
            return self.nodes[self.idx]
        else:
            if self.mode is 'circular':
                self.idx = 0
            else:
                self.idx = len(self.nodes)
                raise StopIteration

    def has_next(self):
        """

        Return true if there are nodes left in dll

        """
        if self.idx < len(self.nodes):
            return True
        else:
            return False

    def previous(self):
        """

        Get the previous coordinate in path

        """

        pass
'''