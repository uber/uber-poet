import argparse
import modulegen
import shutil
import os
import time
import dotreader
import subprocess
import logging
import ConfigParser
import json

from cpulogger import CPULog
from moduletree import ModuleNode, ModuleGenType
from os.path import join


class CommandLineCommon(object):

    @staticmethod
    def gen_graph(gen_type, dot_path=None, module_count=0):
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
            logging.info("Reading dot file: %s", dot_path)
            app_node, node_list = dotreader.DotFileReader().read_dot_file(dot_path)
        else:
            logging.error("Unexpected argument set, aborting.")
            item_list = ', '.join(ModuleGenType.enum_list())
            logging.error("Choose from ({}) module count: {} dot path: {} ".format(item_list, module_count, dot_path))
            raise ValueError("Invalid Arguments")  # TODO better error raising

        return app_node, node_list

    @staticmethod
    def del_old_output_dir(output_directory):
        if os.path.isdir(output_directory):
            # TODO fix this quick overwrite hack, since we should warn/ask on overwrite
            logging.info("Deleting old mock app directory %s", output_directory)
            shutil.rmtree(output_directory)

    @staticmethod
    def make_buckconfig_local(buckconfig_path, build_trace_path, wmo_enabled):
        logging.warn('Overwriting .buckconfig.local file at: %s', buckconfig_path)
        config = ConfigParser.RawConfigParser()
        uber_section = 'uber'
        config.add_section(uber_section)
        config.set(uber_section, 'xcode_tracing_path', build_trace_path)
        config.set(uber_section, 'chrome_trace_build_times', 'true')
        config.set(uber_section, 'whole_module_optimization', str(wmo_enabled))
        config.add_section('project')
        config.set('project', 'ide_force_kill', 'never')

        with open(buckconfig_path, 'w') as buckconfig:
            config.write(buckconfig)

    @staticmethod
    def count_swift_loc(code_path):
        """Returns the number of lines of code in `code_path` using cloc. If cloc is not
        on your system or there is an error, then it returns -1"""
        try:
            logging.info('Counting lines of code in %s', code_path)
            raw_json_out = subprocess.check_output(['cloc', '--quiet', '--json', code_path])
        except OSError:
            logging.warning("You do not have cloc installed, skipping line counting.")
            return -1

        json_out = json.loads(raw_json_out)
        swift_loc = json_out.get('Swift', {}).get('code', 0)
        if not swift_loc:
            logging.error('Unexpected cloc output "%s"', raw_json_out)
            raise ValueError('cloc did not give a correct value')
        return swift_loc

    @staticmethod
    def apply_cpu_to_traces(build_trace_path, cpu_logger):
        # TODO make this only apply to new traces
        logging.info('Applying CPU info to traces in %s', build_trace_path)
        cpu_logs = cpu_logger.process_log()
        trace_paths = [join(build_trace_path, f) for f in os.listdir(build_trace_path) if f.endswith('trace')]
        for trace_path in trace_paths:
            with open(trace_path, 'r') as trace_file:
                traces = json.load(trace_file)
                new_traces = CPULog.apply_log_to_trace(cpu_logs, traces)
            with open(trace_path+'.json', 'w') as new_trace_file:
                json.dump(new_traces, new_trace_file)


class CommandLineMain(object):

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

    def main(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')
        start = time.time()
        _, args = self.make_args()
        dot_path = args.dot_file if hasattr(args, 'dot_file') else None
        module_count = args.module_count if hasattr(args, 'module_count') else 0

        app_node, node_list = CommandLineCommon.gen_graph(args.gen_type, dot_path, module_count)

        CommandLineCommon.del_old_output_dir(args.output_directory)
        gen = modulegen.BuckProjectGenerator(args.output_directory, args.buck_module_path)

        logging.info("Creating a {} module count mock app in {}".format(len(node_list), args.output_directory))
        logging.info("Example command: $ ./monorepo project /{}/App:MockApp".format(args.buck_module_path))
        gen.gen_app(app_node, node_list, args.total_lines_of_code)

        fin = time.time()
        logging.info("Done in %f s", fin-start)
