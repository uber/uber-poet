import os
import argparse
import logging
import subprocess
import time
import datetime
import modulegen
import shutil

from cpulogger import CPULogger
from moduletree import ModuleGenType
from util import makedir, parse_xcode_version, sudo_enabled, check_dependent_commands
from os.path import join
from commandline import CommandLineCommon


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


class CommandLineMultisuite(object):

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Build all mock app types and log times to a log file.')
        parser.add_argument('--log_dir', required=True,
                            help='Where logs such as build times should exist.')
        parser.add_argument('--ios_git_root', required=True,
                            help='Where the ios monorepo checkout is.')

        parser.add_argument('--switch_xcode_versions', action='store_true',
                            help='Switch xcode verions as part of the full multisuite test. Requires sudo.')
        parser.add_argument('--skip_clean', action='store_true',
                            help="Skip calling `./xcode clean`  Still removes the mock app's custom DerivedData folder")
        parser.add_argument('--skip_xcode_build', action='store_true',
                            help='Skips building the mock apps.  Useful for speeding up testing.')
        parser.add_argument('--test_build_only', action='store_true',
                            help='Only builds a small flat build type to create short testing loops.')

        return parser.parse_args()

    def set_args_as_vars(self, args):
        self.log_dir = args.log_dir
        self.ios_git_root = args.ios_git_root
        self.switch_xcode_versions = args.switch_xcode_versions
        self.run_xcodebuild = (not args.skip_xcode_build)
        self.test_build_only = args.test_build_only
        self.skip_clean = args.skip_clean

    def main(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')
        args = self.parse_args()
        self.set_args_as_vars(args)
        self.run_multisuite()

    def make_context(self, log_dir, ios_git_root, test_build):
        self.settings_state = SettingsState(ios_git_root)
        self.log_dir = log_dir
        self.ios_git_root = ios_git_root
        self.monorepo_binary = join(ios_git_root, "monorepo")
        self.xcode_util_binary = join(ios_git_root, "xcode")
        self.mock_app_workspace = join(ios_git_root, 'apps', 'mockapp', 'App', 'MockApp.xcworkspace')
        self.mock_output_dir = join(ios_git_root, 'apps', 'mockapp')
        self.dot_file_path = join(log_dir, 'helix_deps.gv')
        self.build_time_path = join(log_dir, 'build_times.txt')
        self.build_time_csv_path = join(log_dir, 'build_times.csv')
        self.build_trace_path = join(log_dir, 'build_traces')
        self.buckconfig_path = join(ios_git_root, '.buckconfig.local')
        self.buck_path = '/apps/mockapp'
        self.app_buck_path = "/{}/App:MockApp".format(self.buck_path)
        self.xcode_paths = {  # TODO a better way to specify xcode versions to test
            9: '/Applications/Xcode.9.4.1.9F2000.app/',
            10: '/Applications/Xcode-beta.app/',
        }

        if test_build:
            logging.info("Using test build settings")
            self.loc = 15000
            self.wmo_modes = [False]
            self.bs_mod_count = 5
            self.normal_mod_count = 5
            self.type_list = [ModuleGenType.flat]
        else:
            self.loc = 1500000  # 1.5 million loc
            self.wmo_modes = [True, False]
            # TODO a better way to set module count
            self.bs_mod_count = 30  # we only want 30 small modules for big/small gen types
            self.normal_mod_count = 150
            self.type_list = ModuleGenType.enum_list()

    def build_app_type(self, gen_type, wmo_enabled):
        xcode_version, xcode_build_id = parse_xcode_version()
        xcode_name = '{}_'.format(xcode_version.replace('.', '_'))
        build_log_path = join(self.log_dir, '{}{}_mockapp_build_log.txt'.format(xcode_name, gen_type))

        gen_info = '{} (wmo_enabled: {}, xcode_version: {} {})'.format(
            gen_type, wmo_enabled, xcode_version, xcode_build_id)
        logging.info('##### Generating %s', gen_info)
        subprocess.check_call(['xcodebuild', '-version'], stdout=self.build_time_file)

        CommandLineCommon.del_old_output_dir(self.mock_output_dir)

        logging.info('Generating mock app')
        module_count = self.bs_mod_count if 'bs' in gen_type else self.normal_mod_count
        app_node, node_list = CommandLineCommon.gen_graph(gen_type, self.dot_file_path, module_count)
        self.project_generator.gen_app(app_node, node_list, self.loc)

        swift_loc = CommandLineCommon.count_swift_loc(self.mock_output_dir)
        logging.info('App type "%s" generated %d loc', gen_type, swift_loc)

        total_time = 0
        if self.run_xcodebuild:
            logging.info('Generate xcode workspace & clean')

            derived_data_path = '/tmp/ub_mockapp_derived_data'
            shutil.rmtree(derived_data_path, ignore_errors=True)
            makedir(derived_data_path)

            subprocess.check_call([self.monorepo_binary, 'project', self.app_buck_path, '-d'])
            if not self.skip_clean:
                subprocess.check_call([self.xcode_util_binary, 'clean'])

            logging.info('Start xcodebuild')
            start = time.time()
            with open(build_log_path, 'w') as build_log_file:
                subprocess.check_call(['xcodebuild', 'build',
                                       '-scheme', 'MockApp',
                                       '-sdk', 'iphonesimulator',
                                       '-workspace', self.mock_app_workspace,
                                       '-derivedDataPath', derived_data_path],
                                      stdout=build_log_file, stderr=build_log_file)
            end = time.time()
            total_time = int(end-start)
        else:
            logging.info('Skipping xcodebuild')

        build_end = str(datetime.datetime.now())
        log_statement = '{} w/ {} (loc: {}) modules took {} s\n'.format(
            gen_info, len(node_list), swift_loc, total_time)
        logging.info(log_statement)
        self.build_time_file.write(log_statement)
        self.build_time_file.flush()
        full_xcode_version = xcode_version + " " + xcode_build_id
        self.build_time_csv_file.write('{}, {}, {}, {}, {}, {}, {}\n'.format(
            build_end, gen_type, full_xcode_version, wmo_enabled, total_time, len(node_list), swift_loc))
        self.build_time_csv_file.flush()

    def verify_dependencies(self):
        xcode = ['xcodebuild', 'xcode-select']
        local = [self.monorepo_binary, self.xcode_util_binary]
        missing = check_dependent_commands(xcode + local)

        if missing == xcode:
            logging.error("Xcode command line tools do not seem to be installed / are missing in your path.")
        elif missing == local:
            logging.error("ios monorepo commands are missing, did you give the proper repo root?")

        if missing:
            raise OSError("Missing required binaries: {}".format(str(missing)))

    def multisuite_setup(self):
        self.make_context(self.log_dir, self.ios_git_root, self.test_build_only)
        self.settings_state.save_buckconfig_local()
        self.settings_state.save_xcode_select()

        # Don't want to run twice if xcode_switching is disabled
        self.xcode_versions = [9, 10] if self.switch_xcode_versions else [-1]

        self.verify_dependencies()

        makedir(self.log_dir)
        makedir(self.build_trace_path)

        logging.info('Starting build session')
        self.build_time_file = open(self.build_time_path, 'a')
        self.build_time_csv_file = open(self.build_time_csv_path, 'a')

        now = str(datetime.datetime.now())
        self.build_time_file.write('Build session started at {}\n'.format(now))
        self.build_time_file.flush()

        with open(self.dot_file_path, 'w') as dot_file:
            logging.info('Generate dot graph')
            subprocess.check_call([self.monorepo_binary, 'query', "deps(helix)", '--dot'], stdout=dot_file)

        self.project_generator = modulegen.BuckProjectGenerator(self.mock_output_dir, self.buck_path)

    def multisuite_cleanup(self):
        self.build_time_file.close()
        self.build_time_csv_file.close()

        self.settings_state.restore_buckconfig_local()

        if self.switch_xcode_versions:
            self.settings_state.restore_xcode_select()

    def switch_xcode_version(self, xcode_version):
        logging.warning('Switching to xcode version %d', xcode_version)

        if not sudo_enabled():
            logging.warning('I would suggest extending your sudo time out to 1 day so you can do the full suite')
            logging.warning('unattended: https://lifehacker.com/make-sudo-sessions-last-longer-in-linux-1221545774')
            logging.warning("If you don't, then half way through the build suite, it will stall asking for a password.")
            logging.warning("I don't know how to make xcode-select -s not require sudo unfortunately.")

        subprocess.check_call(['sudo', 'xcode-select', '-s', self.xcode_paths[xcode_version]])

    def run_multisuite(self):
        self.multisuite_setup()

        cpu_logger = CPULogger()
        cpu_logger.start()

        for xcode_version in self.xcode_versions:
            if self.switch_xcode_versions:
                self.switch_xcode_version(xcode_version)

            for wmo_enabled in self.wmo_modes:
                logging.info('Swift WMO Enabled: {}'.format(wmo_enabled))
                CommandLineCommon.make_buckconfig_local(self.buckconfig_path, self.build_trace_path, wmo_enabled)

                for gen_type in self.type_list:
                    self.build_app_type(gen_type, wmo_enabled)

        self.multisuite_cleanup()

        cpu_logger.stop()
        CommandLineCommon.apply_cpu_to_traces(self.build_trace_path, cpu_logger)
