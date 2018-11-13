#  Copyright (c) 2017-2018 Uber Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import tempfile
import itertools

from moduletree import ModuleNode
from pprint import pprint
from util import makedir
from collections import defaultdict

# Why filter out modules with these names?
# We are trying to simulate a non-test app build and ignore non-code targets such as asset
# catalogs and schemes. Each module currently gets a static amount of code created for it,
# so non-code modules will add code to the total when they shouldn't if we didn't filter them out.
DOT_MODULES_FILTER = ['test', 'scheme', 'assetcatalog', 'resources', 'fixture', 'needle']


class DotFileReader(object):
    """
    This class reads a dot file from a `buck query "deps(target)" --dot > file.gv` output
    and translates it into a `ModuleNode` dependency graph for the `BuckProjectGenerator` class
    to consume.  The entry point is `DotFileReader.read_dot_file(path)`

    Why make our own dot file parser vs using the two other python libaries available?  They're
    really slow.  Probably because of some extra stuff we don't do.
    """

    def read_dot_file(self, path, root_node_name):
        """Reads a BUCK dependency dump in a dot/gv file at `path` and returns a `ModuleNode`
        graph root and list of nodes to generate a mock app from it."""
        with open(path, 'r') as f:
            text = f.read()

        raw_edges = self.extract_edges(text)
        ident_names = self.identical_names(raw_edges)
        edges = self.clean_edge_names(raw_edges)
        dep_map = self.make_dep_map_from_edges(edges)  # A dep_map is really an outgoing edge map

        # Debug dumps of dot reader state for debugging
        # incoming_map = self.incoming_edge_map_from_dep_map(dep_map)
        # anon_edge = self.anonymize_edge_names(edges, root_node_name)
        # self.debug_dump([edges, raw_edges, anon_edge],[dep_map,ident_names,incoming_map])

        if ident_names:
            logging.error("Found identical buck target names in dot file: %s", path)
            logging.error(str(ident_names))
            raise ValueError("Dot file contains buck target names that are identical, but have different paths")
        else:
            root, nodes = self.mod_graph_from_dep_map(dep_map, root_node_name)
            logging.debug("%s %s total nodes: %d", root, root.deps, len(nodes))
            return root, nodes

    def extract_edges(self, text, filter=True):
        """Converts dot file text with buck targets as edges into a simpler [(string,string)] list.
        Also filters out unwanted target types if `filter=True`.

        Dot files are basically lines of `"string" -> "string";` that represent a list of edges in a
        graph."""
        def edge(line):
            return line[:-1].split('->')

        def name(part):
            return str(part.strip().replace('"', ''))

        def fil(line):
            lower = line.lower()
            bad_word = False
            for k in DOT_MODULES_FILTER:
                if k in lower:
                    bad_word = True
                    break
            return '->' in line and not (filter and bad_word)

        return [[name(part) for part in edge(line)] for line in text.splitlines() if fil(line)]

    def extract_buck_target(self, text):
        """Extracts the target name from a buck target path. Ex: //a/b/c:target -> target
        If the target is invalid, just returns the original text."""
        parts = text.split(":")
        if len(parts) != 2:
            return text
        return parts[1]

    def clean_edge_names(self, edges):
        "Makes edge names only be their buck target name"
        return [[self.extract_buck_target(text) for text in pair] for pair in edges]

    def anonymize_edge_names(self, edges, main_app_module_name):
        """Makes edge names anonymous so you can send them to third parties without
        revealing the names of your modules. """

        # make lib_index an object to avoid a scope quirk of python with inner functions
        # https://www.codesdope.com/blog/article/nested-function-scope-of-variable-closures-in-pyth/
        lib_index = itertools.count()
        name_dict = {main_app_module_name: "DotReaderMainModule"}

        def name(orig):
            if orig not in name_dict:
                name_dict[orig] = 'DotReaderLib' + str(lib_index.next())
            return name_dict[orig]

        return [[name(left), name(right)] for left, right in edges]

    def make_dep_map_from_edges(self, edges):
        "Converts a raw [(origin,destination)] edge list into a {origin:[destinations]} outgoing edge map."
        dep_map = defaultdict(list)
        for pair in edges:
            origin, destination = pair
            dep_map[origin] += [destination]
        return dict(dep_map)

    def incoming_edge_map_from_dep_map(self, dep_map):
        "Converts a outgoing edge map into it's inverse, a {destination:[origins]} incoming edge map."
        incoming = defaultdict(list)
        for node, outgoing in dep_map.iteritems():
            for out in outgoing:
                incoming[out] += [node]

        # Roots wont show up in the incoming list in the above for loop
        roots = set(dep_map.keys()) - set(incoming.keys())
        for root in roots:
            incoming[root] = []

        return dict(incoming)

    def reachability_set(self, dep_map, root_node_name):
        "Returns a set of all nodes reachable from root_node_name"
        seen = set()
        consume_list = [root_node_name]
        while len(consume_list) > 0:
            item = consume_list.pop(0)
            seen.add(item)
            consume_list += dep_map[item]
        return seen

    def find_roots_in_dep_map(self, dep_map):
        """Finds the roots in the DAG represented by a outgoing edge map.
        If it returns empty, then you have cycles and thus don't have a DAG."""
        incoming = self.incoming_edge_map_from_dep_map(dep_map)
        # A node with no incoming edges and some outgoing edges is a root in a DAG
        # Nodes with no edges are not really part of a graph, so we ignore them
        return [node for node, incoming_edges in incoming.iteritems() if not incoming_edges and dep_map[node]]

    def identical_names(self, edges):
        "Returns how many times a buck target name occurs in a edge list, filtering out unique names"
        dep_map = self.make_dep_map_from_edges(edges)
        name_count = {}
        for k in dep_map.keys():
            name = self.extract_buck_target(k)
            name_count[name] = name_count.get(name, 0) + 1

        name_count = {key: value for key, value in name_count.iteritems() if value > 1}
        return name_count

    def biggest_root(self, dep_map):
        """Finds the root with the most reachable nodes under it inside a DAG.
        The biggest root is probably the app tree."""
        roots = self.find_roots_in_dep_map(dep_map)
        root_name = None
        if len(roots) == 1:
            root_name = roots[0]
        elif len(roots) == 0:
            raise ValueError("Cyclic dependency graph given (len(roots) == 0), aborting")
        else:
            max_size = -1
            for r in roots:
                size = len(self.reachability_set(dep_map, r))
                if size > max_size:
                    root_name, max_size = r, size
        return root_name

    def mod_graph_from_dep_map(self, dep_map, root_node_name):
        """Converts an outgoing edge map (`dep_map`) into a ModuleNode graph
        that you can generate a mock app from.  You have to provide the
        root node / application node name (`root_node_name`) for the graph. """
        def make_mod(name):
            return ModuleNode(name, ModuleNode.LIBRARY)

        mod_map = {name: make_mod(name) for name in dep_map.keys()}
        # TODO fix mod_map[self.biggest_root(dep_map)].  If this works you don't
        # have to pass the app node name any more.
        app_node = mod_map[root_node_name]
        app_node.node_type = ModuleNode.APP

        for name, deps in dep_map.iteritems():
            new_deps = []
            for dep_name in deps:
                mod = mod_map.get(dep_name, None)
                if not mod:
                    mod = make_mod(dep_name)
                    mod_map[dep_name] = mod
                new_deps.append(mod)
            mod_map[name].deps = new_deps

        return app_node, mod_map.values()

    def write_struct(self, struct, path):
        "Writes generic python objects to disk (not deserializable)"
        with open(path, 'w') as f:
            pprint(struct, f)

    def write_edges(self, edges, path):
        "Writes edge lists to disk"
        with open(path, 'w') as f:
            for e in edges:
                f.write('"{}" -> "{}";\n'.format(e[0], e[1]))

    def debug_dump(self, edges, structs):
        """
        Dumps various intermediate objects to files to help debugging.
        `edges` will dump dot files of a list of edge pairs. Type: [[(String,String)]]
        `structs` will dump a pretty print of python objects. Type: [PythonObject]
        """
        dump_path = os.path.join(tempfile.gettempdir(), 'ub_dot_graph_dump')
        logging.info('Dumping dotreader.py debug structures to %s', dump_path)
        makedir(dump_path)

        for i, edge in enumerate(edges):
            path = os.path.join(dump_path, 'edges{}.gv'.format(i))
            self.write_edges(edge, path)
        for i, struct in enumerate(structs):
            path = os.path.join(dump_path, 'struct{}.py'.format(i))
            self.write_struct(struct, path)
