import argparse
import modulegen
import shutil
import os
import time
import dotreader
import subprocess
from moduletree import ModuleNode, ModuleGenType
from util import makedir
import datetime
from os.path import join
import logging
import ConfigParser


class CommandLineInterface(object):

    def __init__(self):
        super(CommandLineInterface, self).__init__()

    def make_args(self):
        """Parses command line arguments"""
        arg_desc = 'Generate a fake test project with many buck modules'

        parser = argparse.ArgumentParser(description=arg_desc)

        parser.add_argument('-o', '--output_directory', required=True,
                            help='Where the mock project should be output.')
        parser.add_argument('-bmp', '--buck_module_path', required=True,
                            help='The root of the BUCK dependency path of the generated code.')
        parser.add_argument('-loc', '--total_lines_of_code', type=int, default=1500000,
                            help='How many approx lines of code should be generated.')
        parser.add_argument('-gt', '--gen_type', required=True, choices=ModuleGenType.enum_list(),
                            help='What kind of mock app generation you want.')

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-mc', '--module_count', type=int,
                           help='How many modules your fake app should contain.  In big small (bs_) mock types, it specifies the small module count.')
        group.add_argument('-dot', '--dot_file',
                           help='Generate a project based on a dot file representation from a `buck query "deps(target)" --dot` output')

        return parser, parser.parse_args()

    def gen_graph(self, gen_type, dot_path=None, module_count=0):
        app_node, node_list = None, None

        big_modules = 3
        layer_count = 10

        if gen_type == ModuleGenType.flat:
            app_node, node_list = ModuleNode.gen_flat_graph(module_count)
        elif gen_type == ModuleGenType.bs_flat:
            app_node, node_list = ModuleNode.gen_flat_big_small_graph(big_modules, module_count)
        elif gen_type == ModuleGenType.layered:
            app_node, node_list = ModuleNode.gen_layered_graph(layer_count, module_count / layer_count)
        elif gen_type == ModuleGenType.bs_layered:
            app_node, node_list = ModuleNode.gen_layered_big_small_graph(big_modules, module_count)
        elif dot_path and gen_type == ModuleGenType.dot:
            print "Reading dot file:", dot_path
            app_node, node_list = dotreader.DotFileReader().read_dot_file(dot_path)
        else:
            print "Unexpected argument set, aborting."
            print "Choose from ({})".format(', '.join(ModuleGenType.enum_list())
                                            ), 'module count', module_count, 'dot path', dot_path
            raise ValueError("Invalid Arguments")  # TODO better error raising

        return app_node, node_list

    def del_old_output_dir(self, output_directory):
        if os.path.isdir(output_directory):
            # TODO fix this quick overwrite hack, since we should warn/ask on overwrite
            logging.info("Deleting old mock app directory %s", output_directory)
            shutil.rmtree(output_directory)

    def main(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')
        start = time.time()
        _, args = self.make_args()
        dot_path = args.dot_path if hasattr(args, 'dot_path') else None
        module_count = args.module_count if hasattr(args, 'module_count') else 0
        app_node, node_list = self.gen_graph(args.gen_type, dot_path, module_count)

        self.del_old_output_dir(args.output_directory)
        gen = modulegen.BuckProjectGenerator(args.output_directory, args.buck_module_path)

        logging.info("Creating a {} module count mock app in {}".format(len(node_list), args.output_directory))
        logging.info("Example command: $ ./monorepo project /{}/App:MockApp".format(args.buck_module_path))
        gen.gen_app(app_node, node_list, args.total_lines_of_code)

        fin = time.time()
        logging.info("Done in %f s", fin-start)

    def multisuite(self, log_dir, ios_git_root, switch_xcode=False):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')

        monorepo_binary = join(ios_git_root, "monorepo")
        xcode_util_binary = join(ios_git_root, "xcode")
        mock_app_workspace = join(ios_git_root, 'apps', 'mockapp', 'App', 'MockApp.xcworkspace')
        mock_output_dir = join(ios_git_root, 'apps', 'mockapp')
        dot_file_path = join(log_dir, 'helix_deps.gv')
        build_time_path = join(log_dir, 'build_times.txt')
        build_time_csv_path = join(log_dir, 'build_times.csv')
        build_trace_path = join(log_dir, 'build_traces')
        buckconfig_path = join(ios_git_root, '.buckconfig.local')
        buck_path = '/apps/mockapp'
        app_buck_path = "/{}/App:MockApp".format(buck_path)
        loc = 1500000  # 1.5 million loc
        xcode_paths = {  # TODO a better way to specify xcode versions to test
            9: '/Applications/Xcode.9.4.1.9F2000.app/',
            10: '/Applications/Xcode-beta.app/',
        }

        makedir(log_dir)
        makedir(build_trace_path)

        logging.info('Starting build session')
        build_time_file = open(build_time_path, 'a')
        build_time_csv_file = open(build_time_csv_path, 'a')

        now = str(datetime.datetime.now())
        build_time_file.write('Build session started at {}\n'.format(now))
        build_time_file.flush()

        with open(dot_file_path, 'w') as dot_file:
            logging.info('Generate dot graph')
            subprocess.check_call([monorepo_binary, 'query', "deps(helix)", '--dot'], stdout=dot_file)

        project_generator = modulegen.BuckProjectGenerator(mock_output_dir, buck_path)

        def inner_loop(wmo_enabled, gen_type, xcode_version=''):
            xcode_name = '{}_'.format(xcode_version) if xcode_version else ''
            build_log_path = join(log_dir, '{}{}_mockapp_build_log.txt'.format(xcode_name, gen_type))

            gen_info = '{} (wmo_enabled: {})'.format(gen_type, wmo_enabled)
            logging.info('##### Generating %s', gen_info)
            subprocess.check_call(['xcodebuild', '-version'], stdout=build_time_file)

            self.del_old_output_dir(mock_output_dir)

            logging.info('Generating mock app')
            module_count = 30 if 'bs' in gen_type else 150  # we only want 30 small modules for big/small gen types
            app_node, node_list = self.gen_graph(gen_type, dot_file_path, module_count)
            project_generator.gen_app(app_node, node_list, loc)

            logging.info('Generate xcode workspace & clean')
            subprocess.check_call([monorepo_binary, 'project', app_buck_path, '-d'])
            subprocess.check_call([xcode_util_binary, 'clean'])

            logging.info('Start xcodebuild')
            start = time.time()
            with open(build_log_path, 'w') as build_log_file:
                subprocess.check_call(['xcodebuild', 'build', '-scheme', 'MockApp', '-sdk',
                                       'iphonesimulator', '-workspace', mock_app_workspace],
                                      stdout=build_log_file, stderr=build_log_file)
            end = time.time()

            total_time = int(end-start)
            build_end = str(datetime.datetime.now())
            log_statement = '{} w/ {} modules took {} s\n'.format(gen_info, len(node_list), total_time)
            logging.info(log_statement)
            build_time_file.write(log_statement)
            build_time_file.flush()
            build_time_csv_file.write('{}, {}, {}, {}, {}\n'.format(
                build_end, gen_type, xcode_version, wmo_enabled, total_time))
            build_time_csv_file.flush()

        # Don't want to run twice if xcode_switching is disabled
        xcode_versions = [9, 10] if switch_xcode else [-1]

        for xcode_version in xcode_versions:
            # We do xcode-select first because it requires a sudo
            # I would suggest extending your sudo time out to 1 day so you can do the full suite
            # unattended: https://lifehacker.com/make-sudo-sessions-last-longer-in-linux-1221545774
            # Since I don't know how to not make xcode-select -s require sudo
            xcode_name = ''
            if switch_xcode:
                logging.warning('Switching to xcode version %d', xcode_version)
                subprocess.check_call(['sudo', 'xcode-select', '-s', xcode_paths[xcode_version]])
                xcode_name = xcode_version

            for wmo_enabled in [True, False]:
                logging.info('Swift WMO Enabled: {}'.format(wmo_enabled))
                logging.warn('Overwriting .buckconfig.local file at: %s', buckconfig_path)
                config = ConfigParser.RawConfigParser()
                uber_section = 'uber'
                config.add_section(uber_section)
                config.set(uber_section, 'xcode_tracing_path', build_trace_path)
                config.set(uber_section, 'chrome_trace_build_times', 'true')
                config.set(uber_section, 'whole_module_optimization', str(wmo_enabled))

                with open(buckconfig_path, 'w') as buckconfig:
                    config.write(buckconfig)

                for gen_type in ModuleGenType.enum_list():
                    inner_loop(wmo_enabled, gen_type, xcode_name)

        logging.warn('Removing .buckconfig.local file at: %s', buckconfig_path)
        os.remove(buckconfig_path)
        build_time_file.close()
        build_time_csv_file.close()
