#  Copyright (c) 2021 Uber Technologies, Inc.
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

import os
import tempfile
import unittest
from os.path import join

import mock
import testfixtures.popen
from testfixtures.popen import MockPopen, PopenBehaviour

from uberpoet.filegen import Language
from uberpoet.genproj import GenProjCommandLine
from uberpoet.multisuite import CommandLineMultisuite

from .utils import integration_test, read_file


class TestCocoaPodsIntegration(unittest.TestCase):
    def verify_genproj(self, app_path, dir_file_count, swift_file_count, objc_file_count):
        main_path = join(app_path, 'App')

        # Top level dir
        contents = os.listdir(app_path)
        self.assertGreater(len(contents), 0)
        self.assertEqual(len(contents), dir_file_count)

        swift_file_contents = []
        objc_file_contents = []

        for dirpath, dirnames, filenames in os.walk(app_path):
            for f in filenames:
                ext = os.path.splitext(f)[1]
                if ext == '.swift':
                    swift_file_contents.append(os.path.join(dirpath, f))
                elif ext == '.h' or ext == '.m':
                    objc_file_contents.append(os.path.join(dirpath, f))

        self.assertEqual(len(swift_file_contents), swift_file_count)
        self.assertEqual(len(objc_file_contents), objc_file_count)

        # App dir
        self.assertIn('App', contents)
        app_contents = os.listdir(main_path)
        self.assertGreater(len(app_contents), 0)
        for file_name in ['AppContainer.podspec', 'AppDelegate.swift', 'Info.plist']:
            self.assertIn(file_name, app_contents)
            with open(join(main_path, file_name), 'r') as f:
                self.assertGreater(len(f.read()), 0)
                # TODO actually verify generated code?

    def verify_lib(self, app_path, lib_name, language=Language.SWIFT):
        lib_path = join(app_path, lib_name, 'Sources')

        lib_contents = os.listdir(lib_path)
        self.assertGreater(len(lib_contents), 0)

        if language == Language.SWIFT:
            files = list(['File0.swift'])
        elif language == Language.OBJC:
            files = list(['File0.h', 'File0.m'])

        for f in files:
            self.assertIn(f, lib_contents)
            with open(join(lib_path, f), 'r') as f:
                self.assertGreater(len(f.read()), 0)
                # TODO actually verify generated code?

    @integration_test
    def test_flat_genproj(self):
        app_path = join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = [
            "--output_directory", app_path, "--project_generator_type", "cocoapods", "--gen_type", "flat",
            "--swift_lines_of_code", "150000"
        ]
        command = GenProjCommandLine()
        command.main(args)

        self.verify_genproj(app_path, 104, 902, 0)
        self.verify_lib(app_path, 'MockLib53')

    @integration_test
    def test_genproj_with_objc(self):
        app_path = join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = [
            "--output_directory", app_path, "--project_generator_type", "cocoapods", "--gen_type", "flat",
            "--swift_lines_of_code", "0", "--objc_lines_of_code", "150000"
        ]
        command = GenProjCommandLine()
        command.main(args)

        # 2 Swift file count expected due to main.swift and dummy.swift files for the app target.
        self.verify_genproj(app_path, 104, 2, 2200)
        self.verify_lib(app_path, 'MockLib53', Language.OBJC)

    @integration_test
    def test_dot_genproj(self):
        app_path = join(tempfile.gettempdir(), 'apps', 'mockapp')

        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        args = [
            "--output_directory", app_path, "--project_generator_type", "cocoapods", "--gen_type", "dot",
            "--swift_lines_of_code", "150000", "--dot_file", test_fixture_path, "--dot_root", "DotReaderMainModule"
        ]
        command = GenProjCommandLine()
        command.main(args)

        self.verify_genproj(app_path, 341, 676, 0)
        self.verify_lib(app_path, 'DotReaderLib17')

    @integration_test
    def test_dot_genproj_with_loc_mappings(self):
        app_path = join(tempfile.gettempdir(), 'apps', 'mockapp')
        print(app_path)

        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        loc_test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'loc_mappings.json')
        args = [
            "--output_directory", app_path, "--project_generator_type", "cocoapods", "--gen_type", "dot",
            "--dot_file", test_fixture_path, "--dot_root", "DotReaderMainModule",
            "--loc_json_file_path", loc_test_fixture_path
        ]
        command = GenProjCommandLine()
        command.main(args)

        self.verify_genproj(app_path, 342, 485, 2)
        self.verify_lib(app_path, 'DotReaderLib17')

    @integration_test
    def test_flat_multisuite(self):
        root_path = join(tempfile.gettempdir(), 'multisuite_test')
        app_path = join(root_path, 'apps', 'mockapp')
        log_path = join(root_path, 'logs')
        args = [
            "--log_dir", log_path, "--app_gen_output_dir", root_path, "--test_build_only", "--skip_xcode_build",
            "--project_generator_type", "cocoapods"
        ]
        command = CommandLineMultisuite()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)
        self.verify_genproj(app_path, 103, 602, 0)
        self.verify_lib(app_path, 'MockLib53')

    @integration_test
    def test_flat_multisuite_mocking_calls(self):
        test_cloc_out_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'cloc_out.json')
        cloc_out = read_file(test_cloc_out_path)
        root_path = join(tempfile.gettempdir(), 'multisuite_test')
        app_path = join(root_path, 'apps', 'mockapp')
        log_path = join(root_path, 'logs')
        args = [
            "--log_dir", log_path, "--app_gen_output_dir", root_path, "--test_build_only", "--switch_xcode_versions",
            "--full_clean", "--project_generator_type", "cocoapods"
        ]

        # we need the unused named variable for mocking purposes
        # noinspection PyUnusedLocal
        def command_callable(command, stdin):
            if 'cloc' in command:
                return PopenBehaviour(stdout=cloc_out)
            elif 'xcodebuild -version' in command:
                return PopenBehaviour(stdout=b'Xcode 10.0\nBuild version 10A255\n')
            return PopenBehaviour(stdout=b'test_out', stderr=b'test_error')

        with testfixtures.Replacer() as rep:
            mock_popen = MockPopen()
            rep.replace('subprocess.Popen', mock_popen)
            mock_popen.set_default(behaviour=command_callable)

            with mock.patch('distutils.spawn.find_executable') as mock_find:
                mock_find.return_value = '/bin/ls'  # A non empty return value basically means "I found that executable"
                CommandLineMultisuite().main(args)
                self.assertGreater(os.listdir(app_path), 0)
                self.verify_genproj(app_path, 103, 602, 0)
                self.verify_lib(app_path, 'MockLib53')

    @integration_test
    def test_dot_multisuite(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        root_path = join(tempfile.gettempdir(), 'multisuite_test')
        app_path = join(root_path, 'apps', 'mockapp')
        log_path = join(root_path, 'logs')
        args = [
            "--log_dir", log_path, "--app_gen_output_dir", root_path, "--dot_file", test_fixture_path, "--dot_root",
            "DotReaderMainModule", "--skip_xcode_build", "--test_build_only", "--project_generator_type", "cocoapods"
        ]
        command = CommandLineMultisuite()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)
        self.verify_genproj(app_path, 340, 339, 0)
        self.verify_lib(app_path, 'DotReaderLib17')

    @integration_test
    def test_all_multisuite(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        root_path = join(tempfile.gettempdir(), 'multisuite_test')
        app_path = join(root_path, 'apps', 'mockapp')
        log_path = join(root_path, 'logs')
        args = [
            "--log_dir", log_path, "--app_gen_output_dir", root_path, "--dot_file", test_fixture_path, "--dot_root",
            "DotReaderMainModule", "--skip_xcode_build", "--swift_lines_of_code", "150000",
            "--project_generator_type", "cocoapods"
        ]
        command = CommandLineMultisuite()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)

        # Note we are assuming that the last project to be generated is the dot project.
        # If you change the order of project generation, make this match whatever is the new 'last project'
        # It's a bit fragile, but it's better than not verifying anything currently
        self.verify_genproj(app_path, 340, 676, 0)
        self.verify_lib(app_path, 'DotReaderLib17')
