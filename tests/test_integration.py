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

import os
import tempfile
import unittest

from pearpoet.genproj import GenProjCommandLine
from pearpoet.multisuite import CommandLineMultisuite


def integration_test(func):

    def do_nothing(arg):
        pass

    if 'INTEGRATION' in os.environ:
        return func
    else:
        return do_nothing


class TestIntegration(unittest.TestCase):

    @integration_test
    def test_flat_genproj(self):
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = [
            "--output_directory", app_path, "--buck_module_path", "/apps/mockapp", "--gen_type", "flat",
            "--lines_of_code", "150000"
        ]
        command = GenProjCommandLine()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)

    @integration_test
    def test_dot_genproj(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = [
            "--output_directory", app_path, "--buck_module_path", "/apps/mockapp", "--gen_type", "dot",
            "--lines_of_code", "150000", "--dot_file", test_fixture_path, "--dot_root", "DotReaderMainModule"
        ]
        command = GenProjCommandLine()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)

    @integration_test
    def test_flat_multisuite(self):
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = ["--log_dir", app_path, "--app_gen_output_dir", app_path, "--test_build_only", "--skip_xcode_build"]
        command = CommandLineMultisuite()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)

    @integration_test
    def test_dot_multisuite(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = [
            "--log_dir", app_path, "--app_gen_output_dir", app_path, "--dot_file", test_fixture_path, "--dot_root",
            "DotReaderMainModule", "--skip_xcode_build", "--test_build_only"
        ]
        command = CommandLineMultisuite()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)

    @integration_test
    def test_all_multisuite(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = [
            "--log_dir", app_path, "--app_gen_output_dir", app_path, "--dot_file", test_fixture_path, "--dot_root",
            "DotReaderMainModule", "--skip_xcode_build", "--lines_of_code", "150000"
        ]
        command = CommandLineMultisuite()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)
