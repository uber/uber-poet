import os
import unittest

from uberpoet.locreader import LocFileReader


class TestLocReader(unittest.TestCase):

    def test_read_integration(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'loc_mappings.json')
        lr = LocFileReader()
        lr.read_loc_file(test_fixture_path)

        self.assertEqual(419, lr.loc_for_module("DotReaderLib16"))

    def test_throws_exception_without_read(self):
        lr = LocFileReader()
        self.assertRaises(ValueError, lr.loc_for_module, "DotReaderLib16")
