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

import os.path
import tempfile
import unittest

import mock
import testfixtures.popen

from uberpoet.statemanagement import SettingsState, XcodeManager, XcodeVersion

from .utils import read_file, write_file


def stdoutize(s):
    return b'{}\n'.format(s)


class TestXcodeManager(unittest.TestCase):

    def setUp(self):
        self.mock_popen = testfixtures.popen.MockPopen()
        self.r = testfixtures.Replacer()
        self.r.replace('subprocess.Popen', self.mock_popen)
        self.addCleanup(self.r.restore)

    def test_get_dirs(self):
        x = XcodeManager()
        fake_paths = ['/Applications/Xcode-beta.app', '/Applications/Xcode.app', '/Applications/Chess.app']
        expected_dirs = fake_paths[:2]

        with mock.patch('os.listdir') as mocked_listdir:
            mocked_listdir.return_value = fake_paths
            dirs = x.get_xcode_dirs()
            self.assertEqual(dirs, expected_dirs)

    def test_current_version(self):
        out = b'Xcode 10.0\nBuild version 10A255\n'
        self.mock_popen.set_command('xcodebuild -version', stdout=out)
        version, build = XcodeManager.get_current_xcode_version()
        self.assertEqual(version, '10.0')
        self.assertEqual(build, '10A255')

    def test_module_cache_dir(self):
        base = '/var/folders/sx/0zymnrm13ds1v5n9t4mjdqmr0000gp/C/'
        user = 'testuser'
        clangdir = 'org.llvm.clang.testuser'
        full_path = os.path.join(base, clangdir, 'ModuleCache')

        with mock.patch('getpass.getuser') as mock_getuser:
            mock_getuser.return_value = user
            self.mock_popen.set_command('getconf DARWIN_USER_CACHE_DIR', stdout=stdoutize(base))
            self.assertEqual(full_path, XcodeManager()._get_global_module_cache_dir())

    def test_clean_caches(self):
        self.mock_popen.set_default()
        XcodeManager().clean_caches()
        x = self.mock_popen.mock.method_calls
        self.assertEqual(len(x), 9)

    def test_discover_xcode_versions(self):
        # save_xcode_select / switch_xcode_version
        path = '/Applications/Xcode.app'
        self.mock_popen.set_command('xcode-select -p', stdout=b'{}\n'.format(path))
        self.mock_popen.set_command('sudo xcode-select -s ' + path)

        # get_current_xcode_version
        out = b'Xcode 10.0\nBuild version 10A255\n'
        self.mock_popen.set_command('xcodebuild -version', stdout=out)

        # get_xcode_dirs
        fake_paths = ['/Applications/Xcode.app']
        with mock.patch('os.listdir') as mocked_listdir:
            mocked_listdir.return_value = fake_paths
            versions = XcodeManager().discover_xcode_versions()
            expected = {('10.0', '10A255'): '/Applications/Xcode.app'}
            self.assertEqual(versions, expected)


class TestSettingsState(unittest.TestCase):

    def setUp(self):
        self.mock_popen = testfixtures.popen.MockPopen()
        self.r = testfixtures.Replacer()
        self.r.replace('subprocess.Popen', self.mock_popen)
        self.addCleanup(self.r.restore)

    def test_buckconfig_restore(self):
        tmp = tempfile.gettempdir()
        conf_path = os.path.join(tmp, '.buckconfig.local')
        bak_conf_path = os.path.join(tmp, '.buckconfig.local.bak')
        config_content = 'a = b'
        new_config_content = '1 = 2'
        s = SettingsState(tmp)

        if os.path.isfile(conf_path):
            os.remove(conf_path)
        s.save_buckconfig_local()
        self.assertFalse(os.path.isfile(bak_conf_path))  # no file to save

        write_file(conf_path, config_content)

        for _ in xrange(4):
            s.save_buckconfig_local()
            self.assertTrue(os.path.isfile(bak_conf_path))
            self.assertEqual(read_file(bak_conf_path), config_content)
            write_file(conf_path, new_config_content)
            self.assertEqual(read_file(conf_path), new_config_content)
            s.restore_buckconfig_local()
            self.assertEqual(read_file(conf_path), config_content)

    def test_xcode(self):
        path = '/Applications/Xcode.10.0.0.10A255.app/Contents/Developer'
        self.mock_popen.set_command('xcode-select -p', stdout=stdoutize(path))
        self.mock_popen.set_command('sudo xcode-select -s ' + path)
        tmp = tempfile.gettempdir()
        s = SettingsState(tmp)

        s.save_xcode_select()
        self.assertEqual(s.select_path, path)
        s.restore_xcode_select()


class TestXcodeVersion(unittest.TestCase):

    def test_choose_latest_major_versions_one_version(self):
        data = {('9.4.3', 'ASDF'): '/Applications/Xcode.9.4.3.app', ('10.0', 'QWERT'): '/Applications/Xcode-beta.app'}

        data2 = XcodeVersion.choose_latest_major_versions(data)

        self.assertEqual(data, data2)

    def test_repr(self):
        v = XcodeVersion('2.2.2', 'AAA')
        self.assertEqual(v.__repr__(), "XcodeVersion('2.2.2','AAA')")

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

    def test_xcode_equality(self):
        a = XcodeVersion('1.2.3', 'AAA')
        a2 = XcodeVersion('1.2.3', 'AAA')
        az = XcodeVersion('1.2.3', 'ZZZ')
        b = XcodeVersion('2.2.3', 'AAA')
        a124 = XcodeVersion('1.2.4', 'AAA')
        a125 = XcodeVersion('1.2.5', 'AAA')

        self.assertEqual(a, a2)
        self.assertEqual(a, a)
        self.assertNotEqual(a, az)
        self.assertNotEqual(a, b)
        self.assertNotEqual(b, a2)
        self.assertNotEqual(b, az)

        self.assertFalse(a124.__eq__(a125))
        self.assertFalse(a.__eq__(az))
        self.assertTrue(az.__gt__(a))
        self.assertFalse(a.__gt__(az))
        self.assertTrue(b.__gt__(a))
