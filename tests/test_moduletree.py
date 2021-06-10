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

import unittest

from toposort import toposort_flatten

from uberpoet.moduletree import ModuleNode


class TestModuleTree(unittest.TestCase):

    def test_gen_layered_graph(self):
        root, nodes = ModuleNode.gen_layered_graph(10, 10)
        self.verify_graph(nodes)
        self.assertEqual(len(nodes), 10 * 10 + 1)
        self.assertEqual(ModuleNode.APP, root.node_type)

    def test_gen_bs_layered_graph(self):
        root, nodes = ModuleNode.gen_layered_big_small_graph(10, 10)
        self.verify_graph(nodes)
        self.assertEqual(len(nodes), 19 + 1)
        self.assertEqual(ModuleNode.APP, root.node_type)

    def verify_graph(self, nodes):
        # The generated layered graphs add dependencies randomly to modules within each layer.
        # Because of that, we cannot always specify a fixed expected list of nodes without making
        # tests indeterministic. Instead, we verify topological sorting by re-creating the same graph,
        # sorting it topologicaly and assert the two lists to be the same.
        graph = {n: set(n.deps) for n in nodes}
        self.assertEqual(toposort_flatten(graph), nodes)
