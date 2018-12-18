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

import getpass
import logging
import os
import shutil
import subprocess
import sys
from os.path import join

from .util import pad_list


class SettingsState(object):

    def __init__(self, git_root):
        self.git_root = git_root
        self.have_backed_up = False
        self.local_path = join(self.git_root, '.buckconfig.local')
        self.backup_path = join(self.git_root, '.buckconfig.local.bak')
        self.select_path = None

    def save_buckconfig_local(self):
        if os.path.exists(self.backup_path):
            os.remove(self.backup_path)
        if os.path.exists(self.local_path):
            logging.info('Backing up .buckconfig.local to .buckconfig.local.bak')
            shutil.copy2(self.local_path, self.backup_path)
            self.have_backed_up = True
        else:
            logging.info('No .buckconfig.local to back up, skipping')

    def restore_buckconfig_local(self):
        if self.have_backed_up:
            logging.info('Restoring .buckconfig.local')
            os.remove(self.local_path)
            shutil.copy2(self.backup_path, self.local_path)
            os.remove(self.backup_path)
            self.have_backed_up = False

    def save_xcode_select(self):
        self.select_path = subprocess.check_output(['xcode-select', '-p']).rstrip()

    def restore_xcode_select(self):
        if self.select_path:
            logging.info('Restoring xcode-select path to %s', self.select_path)
            subprocess.check_call(['sudo', 'xcode-select', '-s', self.select_path])


class XcodeManager(object):

    @staticmethod
    def get_xcode_dirs(containing_dir='/Applications'):
        items = os.listdir(containing_dir)
        return [join(containing_dir, d) for d in items if 'xcode' in d.lower() and d.endswith('app')]

    @staticmethod
    def get_current_xcode_version():
        version_out = subprocess.check_output(['xcodebuild', '-version']).splitlines()
        version_num = version_out[0].split(' ')[1]
        build_id = version_out[1].split(' ')[2]
        return version_num, build_id

    @staticmethod
    def switch_xcode_version(xcode_path):
        subprocess.check_call(['sudo', 'xcode-select', '-s', xcode_path])

    def xcode_version_of_path(self, path):
        try:
            self.switch_xcode_version(path)
        except subprocess.CalledProcessError:
            return None, None
        return self.get_current_xcode_version()

    def discover_xcode_versions(self):
        settings = SettingsState('/')
        settings.save_xcode_select()

        candidates = self.get_xcode_dirs()
        out = {}
        for path in candidates:
            version, build = self.xcode_version_of_path(path)
            if version:
                out[(version, build)] = path

        settings.restore_xcode_select()

        out = XcodeVersion.choose_latest_major_versions(out)

        return out

    @staticmethod
    def _get_global_module_cache_dir():
        try:
            username = getpass.getuser()
        except Exception as e:
            sys.exit(str(e))

        cache_dir = subprocess.check_output(['getconf', 'DARWIN_USER_CACHE_DIR']).rstrip()
        user_dir = 'org.llvm.clang.{}'.format(username)
        return os.path.join(cache_dir, user_dir, 'ModuleCache')

    def clean_caches(self):
        logging.info('Cleaning Xcode caches...')

        directories_to_delete = (
            '~/Library/Caches/com.apple.dt.Xcode',
            '~/Library/Developer/Xcode/DerivedData',
            self._get_global_module_cache_dir(),
        )

        for directory in directories_to_delete:
            full_path = os.path.expanduser(directory)
            logging.info('Removing %s', full_path)
            subprocess.check_call(['rm', '-fr', full_path])


class XcodeVersion(object):
    """Represents an xcode version that is comparable"""

    def __init__(self, raw_version, build):
        self.version = self.numeric_version(raw_version)
        self.raw_version = raw_version
        self.build = build

    @staticmethod
    def numeric_version(raw):
        return pad_list([int(x) for x in raw.split('.')], 3, 0)

    @property
    def major(self):
        return self.version[0]

    @property
    def raw(self):
        return self.raw_version, self.build

    @staticmethod
    def choose_latest_major_versions(raw_versions):
        """
        This selects the latest version for each major version of xcode in a set of xcode paths.
        raw_versions is a {(version_str, build_str): xcode_path_str} dictionary.
        """

        versions = {XcodeVersion(raw_version, build): path for (raw_version, build), path in raw_versions.iteritems()}

        major_seperated = {}
        for version, path in versions.iteritems():
            subset = major_seperated.get(version.major, {})
            subset[version] = path
            major_seperated[version.major] = subset

        out = {}
        for subset in major_seperated.values():
            max_version = max(subset.keys())
            out[max_version.raw] = subset[max_version]

        return out

    def __repr__(self):
        return "XcodeVersion('{}','{}')".format(self.raw_version, self.build)

    def __eq__(self, b):
        if not (tuple(self.version) == tuple(b.version)):
            return False
        if self.build == b.build:
            return True
        return False

    def __gt__(self, b):
        if self.version == b.version:
            if self.build > b.build:
                return True
            return False

        if tuple(self.version) > tuple(b.version):
            return True

        return False
