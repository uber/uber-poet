import unittest
from mockappgen.moduletree import ModuleNode


class TestModuleTree(unittest.TestCase):
    def test_gen_layered_graph(self):
        root, nodes = ModuleNode.gen_layered_graph(10, 10)
        self.assertEqual(len(nodes), 10*10 + 1)
        self.assertEqual(ModuleNode.APP, root.node_type)
