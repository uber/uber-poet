#  Copyright (c) 2018 Uber Technologies, Inc.
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

from __future__ import absolute_import

import random

from toposort import toposort_flatten

from .util import merge_lists


class ModuleGenType(object):
    flat = 'flat'
    bs_flat = 'bs_flat'
    layered = 'layered'
    bs_layered = 'bs_layered'
    dot = 'dot'

    @staticmethod
    def enum_list():
        return [
            ModuleGenType.flat,
            ModuleGenType.bs_flat,
            ModuleGenType.layered,
            ModuleGenType.bs_layered,
            ModuleGenType.dot,
        ]


class ModuleNode(object):
    """Represents a module in a dependency graph"""

    APP = 'APP'
    LIBRARY = 'LIBRARY'

    def __init__(self, name, node_type, deps=None):
        super(ModuleNode, self).__init__()
        if deps is None:
            deps = []
        self.name = name
        self.node_type = node_type  # app or library
        self.deps = deps
        # How many code units the module represents.  Bigger modules would
        # have more code units than smaller modules, with 1 being the 'standard' size.
        self.code_units = 1
        self.extra_info = None  # useful for file indexes and such

    def __hash__(self):
        return hash((self.name, self.node_type))

    def __eq__(self, other):
        return (self.name, self.node_type) == (other.name, other.node_type)

    def __repr__(self):
        return "ModuleNode('{}','{}')".format(self.name, self.node_type)

    def __str__(self):
        extra = True if self.extra_info else False
        return "<{} : {} deps: {} has_info: {}>".format(self.name, self.node_type, len(self.deps), extra)

    @staticmethod
    def gen_layered_graph(layer_count, nodes_per_layer, deps_per_node=5):
        """Generates a module dependency graph that has `layer_count` layers,
        with each module only depending on a random selection of the modules
        below it"""

        def node(f_layer, f_node):
            return ModuleNode('MockLib{}_{}'.format(f_layer, f_node), ModuleNode.LIBRARY)

        layers = [[node(l, n) for n in xrange(nodes_per_layer)] for l in xrange(layer_count)]
        app_node = ModuleNode('App', ModuleNode.APP, layers[0])

        node_graph = {}

        for i, layer in enumerate(layers):
            lower_layers = layers[(i + 1):] if i != len(layers) - 1 else []
            lower_merged = merge_lists(lower_layers)
            for node in layer:
                if deps_per_node < len(lower_merged):
                    node.deps = random.sample(lower_merged, deps_per_node)
                else:
                    node.deps = lower_merged

                node_graph[node] = set(node.deps)

        return app_node, (toposort_flatten(node_graph) + [app_node])

    @staticmethod
    def gen_flat_graph(module_count):
        """Generates a module dependency graph that depends on `module_count`
        libraries that don't depend on anything"""
        libraries = [ModuleNode('MockLib{}'.format(i), ModuleNode.LIBRARY) for i in xrange(module_count)]
        app_node = ModuleNode('App', ModuleNode.APP, libraries)

        return app_node, (libraries + [app_node])

    @staticmethod
    def gen_flat_big_small_graph(big_mod_count, small_mod_count):
        big_libs = [ModuleNode('BigMockLib{}'.format(i), ModuleNode.LIBRARY) for i in xrange(big_mod_count)]
        small_libs = [ModuleNode('SmallMockLib{}'.format(i), ModuleNode.LIBRARY) for i in xrange(small_mod_count)]
        app_node = ModuleNode('App', ModuleNode.APP, big_libs + small_libs)

        for l in big_libs:
            l.code_units = 20

        return app_node, (big_libs + small_libs + [app_node])

    @staticmethod
    def gen_layered_big_small_graph(big_mod_count, small_mod_count):
        big_libs = [ModuleNode('AppMockLib{}'.format(i), ModuleNode.LIBRARY) for i in xrange(big_mod_count)]
        app_node = ModuleNode('App', ModuleNode.APP, big_libs)

        layer_count = 3
        layer_mod_count = small_mod_count / layer_count
        deps_per_layer = layer_count / 2 if layer_count >= 2 else 1

        layer_app_node, layer_nodes = ModuleNode.gen_layered_graph(layer_count, layer_mod_count, deps_per_layer)
        layer_nodes = [layer_item for layer_item in layer_nodes if layer_item != layer_app_node]

        for l in big_libs:
            l.code_units = 20
            l.deps = layer_app_node.deps

        node_graph = {n: set(n.deps) for n in big_libs + layer_nodes}
        return app_node, (toposort_flatten(node_graph) + [app_node])
