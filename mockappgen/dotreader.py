from moduletree import ModuleNode
import logging
from pprint import pprint
from util import makedir
from collections import defaultdict


class DotFileReader(object):
    """This class reads a dot file from a `buck query "deps(target)" --dot > file.gv` output 
    and translates it into a `ModuleNode` dependency graph for the `BuckProjectGenerator` class
    to consume.  The entry point is `DotFileReader.read_dot_file(path)` """

    def read_dot_file(self, path):
        """Reads a BUCK dependency dump in a dot/gv file at `path` and returns a `ModuleNode` 
        graph root and list of nodes to generate a mock app from it."""
        with open(path, 'r') as f:
            text = f.read()

        raw_edges = self.extract_edges(text)
        ident_names = self.identical_names(raw_edges)
        edges = self.clean_edge_names(raw_edges)
        dep_map = self.make_dep_map_from_edges(edges)  # A dep_map is really an outgoing edge map

        # incoming_map = self.incoming_edge_map_from_dep_map(dep_map)
        # self.debug_dump([edges, raw_edges],[dep_map,ident_names,incoming_map])

        if ident_names:
            logging.error("Found identical buck target names in dot file: %s", path)
            logging.error(str(ident_names))
            raise ValueError("Dot file contains buck target names that are identical, but have different paths")
        else:
            root, nodes = self.mod_graph_from_dep_map(dep_map)
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
            # Why filter out modules with these names?
            # We are trying to simulate a non-test app build and ignore non-code targets such as asset
            # catalogs and schemes. Each module currently gets a static amount of code created for it,
            # so non-code modules will add code to the total when they shouldn't if we didn't filter them out.
            for k in ['test', 'scheme', 'assetcatalog', 'resources', 'fixture']:
                if k in lower:
                    bad_word = True
                    break
            return '->' in line and not (filter and bad_word)

        return [[name(part) for part in edge(line)] for line in text.splitlines() if fil(line)]

    def extract_buck_target(self, text):
        "Extracts the target name from a buck target path. Ex: //a/b/c:target -> target"
        parts = text.split(":")
        if len(parts) != 2:
            raise ValueError("Unexpected non-buck target string: "+text)
        return parts[1]

    def clean_edge_names(self, edges):
        "Makes edge names only be their buck target name"
        return [[self.extract_buck_target(text) for text in pair] for pair in edges]

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

    def mod_graph_from_dep_map(self, dep_map):
        "Converts an outgoing edge map (`dep_map`) into a ModuleNode graph that you can generate a mock app from"
        def make_mod(name):
            return ModuleNode(name, ModuleNode.LIBRARY)

        mod_map = {name: make_mod(name) for name in dep_map.keys()}
        app_node = mod_map['Helix']  # TODO fix mod_map[self.biggest_root(dep_map)]
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
        "Writes generic python objects to disk"
        with open(path, 'w') as f:
            pprint(struct, f)

    def write_edges(self, edges, path):
        "Writes edge lists to disk"
        with open(path, 'w') as f:
            for e in edges:
                f.write('"{}" -> "{}";\n'.format(e[0], e[1]))

    def debug_dump(self, edges, structs):
        "Dumps various intermediate objects to files to help debugging"
        dump_path = '/tmp/ub_graph_dump/'
        print 'Dumping debug structures to', dump_path
        makedir(dump_path)

        for i, edge in enumerate(edges):
            self.write_edges(edge, '{}edges{}.gv'.format(dump_path, i))
        for i, struct in enumerate(structs):
            self.write_struct(struct, '{}struct{}.py'.format(dump_path, i))
