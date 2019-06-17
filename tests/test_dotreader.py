import os
import unittest

from uberpoet.dotreader import DotFileReader
from uberpoet.moduletree import ModuleNode


class TestDotReader(unittest.TestCase):

    def test_read_integration(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        main_root_name = "DotReaderMainModule"
        dr = DotFileReader()
        root, nodes = dr.read_dot_file(test_fixture_path, main_root_name, is_debug=True)

        self.assertEqual(root.name, main_root_name)
        self.assertEqual(len(nodes), 338)
        self.assertEqual(root.node_type, ModuleNode.APP)
        self.assertIn(root, nodes)
        self.assertEqual(len(root.deps), 1)
        self.assertEqual(len(root.deps[0].deps[0].deps), 5)

        for node in nodes:
            if node.name != main_root_name:
                self.assertEqual(node.node_type, ModuleNode.LIBRARY)
