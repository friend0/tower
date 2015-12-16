from __future__ import (absolute_import, division, print_function, unicode_literals)
import future
from future.utils import viewitems
import sys
from pqdict import PQDict

if sys.version_info[:2] < (2, 7):
    from ordereddict import OrderedDict
else:
    from collections import OrderedDict


class Vertex(dict):
    # __slots__ = []

    def __init__(self, id_, neighborhood=None, prev=None, next_=None):
        """

        Vertex of a graph

        :param neighborhood: A dictionary of neighboring vertices and the weights or their edges.

        """
        self.id = id_
        if neighborhood is None:
            self.dict = {}
        else:
            self.dict = neighborhood
        self.previous = prev
        self.next = next_
        self.visited = False

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v

    def set_previous(self, prev):
        self.previous = prev

    def set_visited(self):
        self.visited = True

    def __str__(self):
        return str(self.id) + ' adjacent: ' + str([x.id for x in self])

    def add_neighbor(self, neighbor, weight=0):
        self[neighbor] = weight

    def remove_neighbor(self, neighbor):
        self.pop(neighbor, None)

    def get_neighbors(self):
        return self.keys()

    def get_id(self):
        return self.id

    def get_weight(self, neighbor):
        return self[neighbor]


class Graph(dict):
    """

    Graph is a set of vertices, potentially connected by edges, which may connect two nodes to each other, or a node
    to itself. The graph is a dictionary of Nodes, where each node has references to a data member, neighbors, and
    start end next in the case of directed graphs.

    """

    def __init__(self, *args, **kwargs):
        """

        Initialize a bare graph unless one is specified as a dictionary.
        :param kwargs: Used to initialize a graph using a dictionary

        """
        super(Graph, self).__init__(*args, **kwargs)

        self.num_vertices = 0

        # take graph input as dictionary and and add to dictionary
        for vertex, neighbors in viewitems(OrderedDict(viewitems(self))):
            self[vertex] = neighbors
            for neighbor, weight in viewitems(neighbors):
                self[vertex][neighbor] = weight

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v

    def __iter__(self):
        return iter(self.values())

    def __setitem__(self, key, val):
        self.num_vertices += 1
        if key not in set(self.keys()):
            dict.__setitem__(self, key, val)
        for key, val in viewitems(val):
            if key not in set(self.keys()):
                self.num_vertices += 1
                dict.__setitem__(self, key, Vertex(key))

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        return val

    def add_vertex(self, vertex):
        """

        Add a vertex to the graph
        :param vertex:

        """
        self[vertex.id] = vertex
        return vertex.id

    def add_vertices(self, vertices):
        """

        Add a list of vertices
        :param vertices: a list of vertices to be added
        :return:

        """
        for vertex in vertices:
            self.num_vertices += 1
            new_vertex = Vertex(vertex)
            self[vertex] = new_vertex
            return new_vertex.id

    def get_vertex(self, id_):
        """

        If there is a vertex matching the given id, return that vertex
        :param id_: The id of the vertex to be returned

        """
        if id_ in self:
            return self[id_]
        else:
            return None

    def get_vertices(self):
        """

        Returns the vertices of the graph

        """

        return self.keys()

    def remove_vertex(self, key):
        self.num_vertices -= 1
        self.pop(key, None)

    def add_edge(self, frm, to, weight=0):
        """

        Connect vertex 'from' to node 'to' and vice versa
        :param frm: Vertex to be connected to 'to'
        :param to: Vertex to be connected to 'from'
        :param weight: The weight of the edge to be created between 'from' and 'to'

        """
        if frm not in self:
            self.add_vertex(frm)
        if to not in self:
            self.add_vertex(to)
        self[frm][to] = weight
        self[to][frm] = weight

    def remove_edge(self, frm, to):
        """

        Remove the edge between vertex 'from' and vertex 'to'
        :param frm:
        :param to:

        """
        if frm not in self:
            self.add_vertex(frm)
        if to not in self:
            self.add_vertex(to)
        self[frm].remove_neighbor(self[to])
        self[to].remove_neighbor(self[frm])

    def get_edges(self):
        """

         A static method generating the edges of the graph "graph". Edges are represented as sets with one
         (a loop back to the vertex) or two vertices.

        """
        edges = []
        for key, vertex in viewitems(self):
            for neighbor in vertex:
                if set((key, neighbor)) not in edges and self[key][neighbor] > 0:
                    edges.append((key, neighbor))
        return edges

    def find_path(self, start_vertex, end_vertex, path=[]):
        """

        Find a path from start_vertex to end_vertex in graph

        """
        graph = self
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return None
        for vertex in graph.keys():
            if vertex not in path:
                extended_path = self.find_path(vertex, end_vertex, path)
                if extended_path:
                    return extended_path
        return None

    def dijkstra(self, start, end):
        """
        Find shortest paths from the  start vertex to all vertices nearer than or equal to the end.

        The input graph G is assumed to have the following representation:
        A vertex can be any object that can be used as an index into a dictionary.
        G is a dictionary, indexed by vertices.  For any vertex v, G[v] is itself a dictionary,
        indexed by the neighbors of v.  For any edge v->w, G[v][w] is the length of the edge.
        This is related to the representation in <http://www.python.org/doc/essays/graphs.html>
        where Guido van Rossum suggests representing graphs as dictionaries map vertices
        to lists of outgoing edges, however dictionaries of edges have many advantages over lists:
        they can store extra information (here, the lengths), they support fast existence playground,
        and they allow easy modification of the graph structure by edge insertion and removal.
        Such modifications are not needed here but are important in many other graph algorithms.
        Since dictionaries obey iterator protocol, a graph represented as described here could
        be handed without modification to an algorithm expecting Guido's graph representation.

        Of course, G and G[v] need not be actual Python dict objects, they can be any other
        type of object that obeys dict protocol, for instance one could use a wrapper in which vertices
        are URLs of web pages and a call to G[v] loads the web page and finds its outgoing links.

        The output is a pair (D,P) where D[v] is the distance from start to v and P[v] is the
        predecessor of v along the shortest path from s to v.

        Dijkstra's algorithm is only guaranteed to work correctly when all edge lengths are positive.
        This code does not verify this property for all edges (only the edges examined until the end
        vertex is reached), but will correctly compute shortest paths even for some graphs with negative
        edges, and will raise an exception if it discovers that a negative edge has caused it to make a mistake.

        :param start: key to starting node
        :param end: key to ending node
        :return: The output is a pair (D,P) where D[v] is the distance from start to v and P[v] is the
        predecessor of v along the shortest path from s to v.
        """

        d = {}  # dictionary of final distances
        p = {}  # dictionary of predecessors
        q = PQDict()  # estimated distances of non-final vertices
        q[start] = 0
        for v_ in q:
            d[v_] = q[v_]
            if v_ == end:
                break
            for w in self[v_]:
                vwLength = d[v_] + self[v_][w]
                if w in d:
                    if vwLength < d[w]:
                        raise ValueError("Dijkstra: found better path to already-final vertex")
                elif w not in q or vwLength < q[w]:
                    q[w] = vwLength
                    p[w] = v_
        return d, p

    def shortest_path(self, start, end):
        """
        Find a single shortest path from the given start vertex to the given end vertex.
        The input has the same conventions as Dijkstra().
        The output is a list of the vertices in order along the shortest path.
        :param start: starting node
        :param end: ending node
        :return:
        """
        d, p = self.dijkstra(start, end)
        path = []
        while 1:
            path.append(end)
            if end == start: break
            end = p[end]
        path.reverse()
        return path

class Path(object):
    """

    Formally, can be understood to represent a simply connected, directed graph.

    """

    origin = None
    destination = None

    def __init__(self, vertices=[]):
        self.num_vertices = len(vertices)
        self.vertices = vertices
        self.origin = vertices[0]
        self.destination = vertices[-1]
        self.idx = -1

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """

        Get the next Coord in path

        """
        if self.idx < len(self.vertices) - 1:
            self.idx += 1
            return self.vertices[self.idx]
        else:
            self.idx = len(self.vertices)
            raise StopIteration

    def has_next(self):
        """

        Return true if there are more nodes after current node in dll

        """
        if self.idx < len(self.vertices) - 1:
            return True
        else:
            return False

    def previous(self):
        """

        Get the previous coordinate in path

        """

        if self.idx > 0:
            self.idx -= 1
            return self.vertices[self.idx]
        else:
            raise StopIteration

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


if __name__ == '__main__':

    G = {'s': {'u': 10, 'x': 5},
         'u': {'v': 1, 'x': 2},
         'v': {'y': 4},
         'x': {'u': 3, 'v': 9, 'y': 2},
         'y': {'s': 7, 'v': 6}}


    g = Graph(G)
    print(g)
    print(g.dijkstra('s'))
    print(g.shortest_path('s', 'v'), type(g.shortest_path('s', 'v')), "Shortest")
    for v in g:
        print(v)
