import unittest
from pearpoet.statemanagement import XcodeVersion


class TestXcode(unittest.TestCase):
    def test_choose_latest_major_versions_one_version(self):
        data = {
            ('9.4.3', 'ASDF'): '/Applications/Xcode.9.4.3.app',
            ('10.0', 'QWERT'): '/Applications/Xcode-beta.app'
        }

        data2 = XcodeVersion.choose_latest_major_versions(data)

        self.assertEqual(data, data2)

    def test_choose_latest_major_versions_one_item(self):
        data = {
            ('9.4.3', 'ASDF'): '/Applications/Xcode.app',
        }

        data2 = XcodeVersion.choose_latest_major_versions(data)

        self.assertEqual(data, data2)

    def test_choose_latest_major_versions_multiple_majors(self):
        data = {
            ('9.5', 'ZZZZ'): '/Applications/Xcode.9.5.app',
            ('9.4.3', 'ASDF'): '/Applications/Xcode.9.4.3.app',
            ('9.2.3', 'JJJJ'): '/Applications/Xcode.9.2.3.app',
            ('10.0', 'AAAA'): '/Applications/Xcode-beta2.app',
            ('10.0', 'BBBB'): '/Applications/Xcode-beta.app',
            ('8.3.1', 'QWERT'): '/Applications/Xcode.8.3.1.app'
        }

        data_after = {
            ('9.5', 'ZZZZ'): '/Applications/Xcode.9.5.app',
            ('10.0', 'BBBB'): '/Applications/Xcode-beta.app',
            ('8.3.1', 'QWERT'): '/Applications/Xcode.8.3.1.app'
        }

        data2 = XcodeVersion.choose_latest_major_versions(data)

        self.assertEqual(data_after, data2)
