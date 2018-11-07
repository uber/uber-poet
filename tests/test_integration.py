import unittest
import os
import tempfile
from mockappgen.genproj import GenProjCommandLine
from mockappgen.multisuite import CommandLineMultisuite


class TestIntegration(unittest.TestCase):
    def test_flat_genproj(self):
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = ["--output_directory", app_path,
                "--buck_module_path", "/apps/mockapp",
                "--gen_type", "flat",
                "--lines_of_code", "150000"]
        command = GenProjCommandLine()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)

    def test_dot_genproj(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = ["--output_directory", app_path,
                "--buck_module_path", "/apps/mockapp",
                "--gen_type", "dot",
                "--lines_of_code", "150000",
                "--dot_file", test_fixture_path,
                "--dot_root", "DotReaderMainModule"]
        command = GenProjCommandLine()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)

    def test_flat_multisuite(self):
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = ["--log_dir", app_path,
                "--app_gen_output_dir", app_path,
                "--test_build_only",
                "--skip_xcode_build"]
        command = CommandLineMultisuite()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)

    def test_dot_multisuite(self):
        test_fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_dot.gv')
        app_path = os.path.join(tempfile.gettempdir(), 'apps', 'mockapp')
        args = ["--log_dir", app_path,
                "--app_gen_output_dir", app_path,
                "--dot_file", test_fixture_path,
                "--dot_root", "DotReaderMainModule",
                "--test_build_only",
                "--skip_xcode_build"]
        command = CommandLineMultisuite()
        command.main(args)
        self.assertGreater(os.listdir(app_path), 0)
