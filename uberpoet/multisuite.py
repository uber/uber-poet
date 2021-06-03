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

from __future__ import absolute_import, print_function

import argparse
import datetime
import logging
import shutil
import subprocess
import sys
import tempfile
import time
from os.path import join

from . import blazeprojectgen, commandlineutil, cpprojectgen
from .cpulogger import CPULogger
from .moduletree import ModuleGenType
from .statemanagement import SettingsState, XcodeManager
from .util import check_dependent_commands, grab_mac_marketing_name, makedir, sudo_enabled


class CommandLineMultisuite(object):

    @staticmethod
    def parse_config(args):
        tmp_root = join(tempfile.gettempdir(), 'mock_app_gen_out')
        log_root = join(tmp_root, 'logs')

        parser = argparse.ArgumentParser(
            description='Build all mock app types and log times & traces to a log file. '
            'Useful as a benchmark suite to compare build performance of different computers.')

        parser.add_argument('--log_dir', default=log_root, help="Where logs such as build times should exist."),
        parser.add_argument(
            '--app_gen_output_dir', default=tmp_root, help="Where generated mock apps should be outputted to."),
        parser.add_argument('--buck_command', default='buck', help="The path to the Buck binary.  Defaults to `buck`."),
        parser.add_argument(
            '--bazel_command', default='bazel', help="The path to the Bazel binary.  Defaults to `bazel`."),
        parser.add_argument(
            '--pod_command', default='pod', help="The path to the CocoaPods binary.  Defaults to `pod`."),

        commandlineutil.AppGenerationConfig.add_app_gen_options(parser)

        actions = parser.add_argument_group('Extra Actions')
        actions.add_argument(
            '--trace_cpu', action='store_true', default=False,
            help="If we should add cpu utilization to build traces."),
        actions.add_argument(
            '--switch_xcode_versions',
            action='store_true',
            default=False,
            help="Switch Xcode versions as part of the full multisuite test. This will search your "
            "`/Applications` directory for xcode.app bundles to build with. Requires sudo."),
        actions.add_argument(
            '--full_clean',
            action='store_true',
            default=False,
            help="Clean all default xcode cache directories to prevent cache effects changing test results."),

        parser.add_argument(
            '--project_generator_type',
            choices=['buck', 'bazel', 'cocoapods'],
            default='buck',
            required=False,
            help='The project generator type to use. Supported types are Buck, Bazel and CocoaPods. Default is `buck`')

        testing = parser.add_argument_group('Testing Shortcuts')
        testing.add_argument(
            '--skip_xcode_build',
            action='store_true',
            default=False,
            help="Skips building the mock apps.  Useful for speeding up testing and making "
            "integration tests independent of non-python dependencies."),
        testing.add_argument(
            '--test_build_only',
            action='store_true',
            default=False,
            help="Only builds a small flat build type to create short testing loops."),

        out = parser.parse_args(args)
        commandlineutil.AppGenerationConfig.validate_app_gen_options(out)

        return out

    # noinspection PyAttributeOutsideInit
    def config_to_vars(self, config):
        self.app_gen_options = commandlineutil.AppGenerationConfig()
        self.app_gen_options.pull_from_args(config)

        self.log_dir = config.log_dir
        self.output_dir = config.app_gen_output_dir
        self.buck_binary = config.buck_command
        self.bazel_binary = config.bazel_command
        self.pod_binary = config.pod_command

        self.project_generator_type = config.project_generator_type

        logging.info('Log output directory: %s', self.log_dir)
        logging.info('Mock app gen output directory: %s', self.output_dir)

        self.trace_cpu = config.trace_cpu
        self.switch_xcode_versions = config.switch_xcode_versions
        self.full_clean = config.full_clean
        self.run_xcodebuild = (not config.skip_xcode_build)
        self.test_build_only = config.test_build_only

    def main(self, args=None):
        if args is None:
            args = sys.argv[1:]
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')

        args = self.parse_config(args)
        self.config_to_vars(args)

        try:
            self.run_multisuite()
        except Exception as e:
            print(e)
        finally:
            self.multisuite_cleanup()
            logging.info("Done")

    # noinspection PyAttributeOutsideInit
    def make_context(self, log_dir, output_dir, test_build):
        self.cpu_logger = CPULogger()
        self.xcode_manager = XcodeManager()
        self.settings_state = SettingsState(output_dir)

        self.log_dir = log_dir
        self.output_dir = output_dir

        self.mock_output_dir = join(output_dir, 'apps', 'mockapp')
        self.mock_pods_app_project = join(self.mock_output_dir, 'Pods', 'Pods.xcodeproj')
        self.mock_app_workspace = join(self.mock_output_dir, 'App', 'App.xcworkspace')
        self.buckconfig_path = join(output_dir, '.buckconfig.local')

        self.sys_info_path = join(log_dir, 'system_info.txt')
        self.build_time_path = join(log_dir, 'build_times.txt')
        self.build_time_csv_path = join(log_dir, 'build_times.csv')
        self.build_trace_path = join(log_dir, 'build_traces')
        self.app_path = '/apps/mockapp'
        self.app_blaze_path = "//App:App"

        has_dot = self.app_gen_options.dot_file_path and self.app_gen_options.dot_root_node_name
        if test_build:
            logging.info("Using test build settings")
            self.app_gen_options.swift_lines_of_code = 100000
            self.wmo_modes = [False]
            self.type_list = [ModuleGenType.dot] if has_dot else [ModuleGenType.flat]
        else:
            self.wmo_modes = [True, False]
            self.type_list = ModuleGenType.enum_list()
            if not has_dot:
                logging.warning("Removing dot mock app type due to lack of dot file to read. "
                                "Specify one in the command line options.")
                self.type_list.remove(ModuleGenType.dot)

    def build_app_type(self, gen_type, wmo_enabled):
        xcode_version, xcode_build_id = XcodeManager.get_current_xcode_version()
        xcode_name = '{}_'.format(xcode_version.replace('.', '_'))
        build_log_path = join(self.log_dir, '{}{}_mockapp_build_log.txt'.format(xcode_name, gen_type))

        gen_info = '{} (wmo_enabled: {}, xcode_version: {} {})'.format(gen_type, wmo_enabled, xcode_version,
                                                                       xcode_build_id)
        logging.info('##### Generating %s', gen_info)

        self.project_generator.use_wmo = wmo_enabled
        commandlineutil.del_old_output_dir(self.mock_output_dir)

        logging.info('Generating mock app')
        app_node, node_list = commandlineutil.gen_graph(gen_type, self.app_gen_options)
        self.project_generator.gen_app(app_node, node_list, self.app_gen_options.swift_lines_of_code,
                                       self.app_gen_options.objc_lines_of_code, self.app_gen_options.loc_json_file_path)

        swift_loc = commandlineutil.count_loc(self.mock_output_dir)
        logging.info('App type "%s" generated %d loc', gen_type, swift_loc)

        # Build App
        total_time = 0
        if self.run_xcodebuild:
            logging.info('Generate workspace & clean')

            derived_data_path = join(tempfile.gettempdir(), 'ub_mockapp_derived_data')
            shutil.rmtree(derived_data_path, ignore_errors=True)
            makedir(derived_data_path)

            if self.project_generator_type == "cocoapods":
                subprocess.check_call([self.pod_binary, 'install'], cwd=self.mock_output_dir)

            if self.full_clean:
                self.xcode_manager.clean_caches()

            logging.info('Start build')
            start = time.time()
            with open(build_log_path, 'w') as build_log_file:
                if self.project_generator_type == "buck":
                    subprocess.check_call([self.buck_binary, 'build', '//...'], cwd=self.mock_output_dir)
                elif self.project_generator_type == "bazel":
                    subprocess.check_call(
                        [self.bazel_binary, 'build', '//...', '--incompatible_require_linker_input_cc_api=false'],
                        cwd=self.mock_output_dir,
                        stdout=build_log_file,
                        stderr=build_log_file)
                elif self.project_generator_type == "cocoapods":
                    subprocess.check_call([
                        'xcodebuild', 'build', '-scheme', 'AppContainer-App', '-sdk', 'iphonesimulator', '-project',
                        self.mock_pods_app_project, '-derivedDataPath', derived_data_path
                    ],
                                          stdout=build_log_file,
                                          stderr=build_log_file)
            end = time.time()
            total_time = int(end - start)
        else:
            logging.info('Skipping build & project generation')

        # Log Results
        build_end = str(datetime.datetime.now())
        log_statement = '{} w/ {} (loc: {}) modules took {} s\n'.format(gen_info, len(node_list), swift_loc, total_time)
        logging.info(log_statement)
        self.build_time_file.write(log_statement)
        self.build_time_file.flush()
        full_xcode_version = xcode_version + " " + xcode_build_id
        self.build_time_csv_file.write('{}, {}, {}, {}, {}, {}, {}\n'.format(
            build_end, gen_type, full_xcode_version, wmo_enabled, total_time, len(node_list), swift_loc))
        self.build_time_csv_file.flush()

    def verify_dependencies(self):
        if not self.run_xcodebuild or self.project_generator_type == "cocoapods":
            return  # We don't need these binaries if we are not going to use them.

        xcode = ['xcodebuild', 'xcode-select']
        local = []
        if self.project_generator_type == "buck":
            local.append(self.buck_binary)
        elif self.project_generator_type == "bazel":
            local.append(self.bazel_binary)
        elif self.project_generator_type == "cocoapods":
            local.append(self.pod_binary)
        missing = check_dependent_commands(xcode + local)

        if missing == xcode:
            logging.error("Xcode command line tools do not seem to be installed / are missing in your path.")
        elif missing == [self.buck_binary]:
            logging.error("Specified buck command not available.  Did you install it in your path?")
        elif missing == [self.bazel_binary]:
            logging.error("Specified bazel command not available.  Did you install it in your path?")
        elif missing == [self.pod_binary]:
            logging.error("Specified pod command not available.  Did you install it in your path?")

        if missing:
            logging.error("Missing required binaries: %s", str(missing))
            raise OSError("Missing required binaries: {}".format(missing))

    def dump_system_info(self):
        logging.info('Recording device info')
        with open(self.sys_info_path, 'w') as info_file:
            info_file.write(grab_mac_marketing_name())
            info_file.write('\n')
            info_file.flush()
            subprocess.check_call(['system_profiler', 'SPHardwareDataType', '-detailLevel', 'mini'], stdout=info_file)
            subprocess.check_call(['sw_vers'], stdout=info_file)

    # noinspection PyAttributeOutsideInit
    def multisuite_setup(self):
        self.make_context(self.log_dir, self.output_dir, self.test_build_only)
        if self.project_generator_type == "buck":
            self.settings_state.save_buckconfig_local()
        self.settings_state.save_xcode_select()

        if self.switch_xcode_versions:
            self.sudo_warning()
            self.xcode_paths = self.xcode_manager.discover_xcode_versions()
            self.xcode_versions = self.xcode_paths.keys()
            logging.info("Discovered xcode versions: %s", str(self.xcode_versions))
        else:
            self.xcode_paths = {}
            self.xcode_versions = [None]

        for path in [self.log_dir, self.build_trace_path, self.output_dir]:
            makedir(path)

        logging.info('Starting build session')
        self.build_time_file = open(self.build_time_path, 'a')
        self.build_time_csv_file = open(self.build_time_csv_path, 'a')

        now = str(datetime.datetime.now())
        self.build_time_file.write('Build session started at {}\n'.format(now))
        self.build_time_file.flush()

        self.dump_system_info()

        print(self.project_generator_type)
        if self.project_generator_type == "buck" or self.project_generator_type == "bazel":
            self.project_generator = blazeprojectgen.BlazeProjectGenerator(
                self.mock_output_dir, self.app_path, flavor=self.project_generator_type)
        elif self.project_generator_type == "cocoapods":
            self.project_generator = cpprojectgen.CocoaPodsProjectGenerator(self.mock_output_dir)
        else:
            raise ValueError("Unknown project generator type: " + str(self.project_generator_type))

        self.verify_dependencies()

    def multisuite_cleanup(self):
        logging.info("Cleaning up multisuite build test")
        if self.project_generator_type == "buck":
            self.settings_state.restore_buckconfig_local()

        if self.switch_xcode_versions:
            self.settings_state.restore_xcode_select()

        if self.build_time_file:
            self.build_time_file.close()
        if self.build_time_csv_file:
            self.build_time_csv_file.close()
        if self.trace_cpu:
            self.cpu_logger.kill()

    @staticmethod
    def sudo_warning():
        if not sudo_enabled():
            logging.warning('I would suggest executing this in a bash script and adding a sudo keep alive so you')
            logging.warning('can run this fully unattended: https://gist.github.com/cowboy/3118588')
            logging.warning("If you don't, then half way through the build suite, it will stall asking for a password.")
            logging.warning("I don't know how to make xcode-select -s not require sudo unfortunately.")

    def switch_xcode_version(self, xcode_version):
        logging.warning('Switching to xcode version %s', str(xcode_version))
        self.xcode_manager.switch_xcode_version(self.xcode_paths[xcode_version])

    def run_multisuite(self):
        self.multisuite_setup()

        start_time = time.time()
        if self.trace_cpu:
            self.cpu_logger.start()

        if self.project_generator_type == "buck":
            commandlineutil.make_custom_buckconfig_local(self.buckconfig_path)

        for xcode_version in self.xcode_versions:
            if self.switch_xcode_versions:
                self.switch_xcode_version(xcode_version)

            for wmo_enabled in self.wmo_modes:
                logging.info('Swift WMO Enabled: {}'.format(wmo_enabled))

                for gen_type in self.type_list:
                    self.build_app_type(gen_type, wmo_enabled)

        if self.trace_cpu:
            self.cpu_logger.stop()
            commandlineutil.apply_cpu_to_traces(self.build_trace_path, self.cpu_logger, start_time)


def main():
    CommandLineMultisuite().main()


if __name__ == '__main__':
    main()
