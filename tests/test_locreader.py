import os
import unittest

from uberpoet.filegen import Language
from uberpoet.locreader import LocFileReader


class TestLocReader(unittest.TestCase):

    def test_loc_for_module(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'loc_mappings.json')
        lr = LocFileReader()
        lr.read_loc_file(test_fixture_path)

        self.assertEqual(419, lr.loc_for_module("DotReaderLib16"))

    def test_language_for_module(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'loc_mappings.json')
        lr = LocFileReader()
        lr.read_loc_file(test_fixture_path)

        self.assertEqual(Language.OBJC, lr.language_for_module("DotReaderLib0"))
        self.assertEqual(Language.SWIFT, lr.language_for_module("DotReaderLib16"))

    def test_throws_exception_without_read(self):
        lr = LocFileReader()
        self.assertRaises(ValueError, lr.loc_for_module, "DotReaderLib16")
