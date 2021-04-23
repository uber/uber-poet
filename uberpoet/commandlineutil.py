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

import ConfigParser
import json
import logging
import os
import shutil
import subprocess
from os.path import join

from . import dotreader
from .cpulogger import CPULog
from .moduletree import ModuleGenType, ModuleNode
from .util import bool_xor


class AppGenerationConfig(object):

    def __init__(self,
                 module_count=0,
                 big_module_count=0,
                 small_module_count=0,
                 lines_of_code=0,
                 app_layer_count=0,
                 dot_file_path='',
                 dot_root_node_name=''):
        self.module_count = module_count
        self.big_module_count = big_module_count
        self.small_module_count = small_module_count
        self.lines_of_code = lines_of_code
        self.app_layer_count = app_layer_count
        self.dot_file_path = dot_file_path
        self.dot_root_node_name = dot_root_node_name

    def pull_from_args(self, args):
        self.validate_app_gen_options(args)
        self.module_count = args.module_count
        self.big_module_count = args.big_module_count
        self.small_module_count = args.small_module_count
        self.lines_of_code = args.lines_of_code
        self.app_layer_count = args.app_layer_count
        self.dot_file_path = args.dot_file_path
        self.dot_root_node_name = args.dot_root_node_name

    @staticmethod
    def add_app_gen_options(parser):
        app = parser.add_argument_group('Mock app generation options')
        app.add_argument(
            '--module_count', default=100, type=int, help="How many modules should be in a normal mock app type."),
        app.add_argument(
            '--big_module_count',
            default=3,
            type=int,
            help="How many big modules should be in a big/small mock app type."),
        app.add_argument(
            '--small_module_count',
            default=50,
            type=int,
            help="How many small modules should be in a big/small mock app type."),
        app.add_argument(
            '--lines_of_code',
            default=1500000,  # 1.5 million lines of code
            type=int,
            help="Approximately how many lines of code each mock app should be."),
        app.add_argument(
            '--app_layer_count',
            default=10,
            type=int,
            help='How many module layers there should be in the layered mock app type.')

        dot = parser.add_argument_group('Dot file mock app config')
        dot.add_argument(
            '--dot_file_path',
            default='',
            type=str,
            help="The path to the dot file to create a mock module graph from.  This dot file should come "
            "from a buck query like so: `buck query \"deps(target)\" --dot > file.gv`.")
        dot.add_argument(
            '--dot_root_node_name',
            default='',
            type=str,
            help="The name of the root application node of the dot file, such as 'App'")

    @staticmethod
    def validate_app_gen_options(args):
        if bool_xor(args.dot_file_path, args.dot_root_node_name):
            logging.info('dot_file_path: "%s" dot_root_node_name: "%s"', args.dot_file_path, args.dot_root_node_name)
            raise ValueError('If you specify a dot file config option, you also have to specify the other one')


def gen_graph(gen_type, config):
    # app_node, node_list = None, None
    modules_per_layer = config.module_count / config.app_layer_count

    if gen_type == ModuleGenType.flat:
        app_node, node_list = ModuleNode.gen_flat_graph(config.module_count)
    elif gen_type == ModuleGenType.bs_flat:
        app_node, node_list = ModuleNode.gen_flat_big_small_graph(config.big_module_count, config.small_module_count)
    elif gen_type == ModuleGenType.layered:
        app_node, node_list = ModuleNode.gen_layered_graph(config.app_layer_count, modules_per_layer)
    elif gen_type == ModuleGenType.bs_layered:
        app_node, node_list = ModuleNode.gen_layered_big_small_graph(config.big_module_count, config.small_module_count)
    elif gen_type == ModuleGenType.dot and config.dot_file_path and config.dot_root_node_name:
        logging.info("Reading dot file: %s", config.dot_file_path)
        app_node, node_list = dotreader.DotFileReader().read_dot_file(config.dot_file_path, config.dot_root_node_name)
    else:
        logging.error("Unexpected argument set, aborting.")
        item_list = ', '.join(ModuleGenType.enum_list())
        logging.error("Choose from ({}) module count: {} dot path: {} ".format(item_list, config.module_count,
                                                                               config.dot_path))
        raise ValueError("Invalid Arguments")

    return app_node, node_list


def del_old_output_dir(output_directory):
    if os.path.isdir(output_directory):
        logging.warning("Deleting old mock app directory %s", output_directory)
        shutil.rmtree(output_directory)


def make_custom_buckconfig_local(buckconfig_path):
    logging.warn('Overwriting .buckconfig.local file at: %s', buckconfig_path)
    config = ConfigParser.RawConfigParser()
    config.add_section('project')
    config.set('project', 'ide_force_kill', 'never')
    config.add_section('parser')
    config.set('parser', 'polyglot_parsing_enabled', 'true')
    config.set('parser', 'default_build_file_syntax', 'SKYLARK')

    with open(buckconfig_path, 'w') as buckconfig:
        config.write(buckconfig)


def count_loc(code_path):
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


def apply_cpu_to_traces(build_trace_path, cpu_logger, time_cutoff=None):
    logging.info('Applying CPU info to traces in %s', build_trace_path)
    cpu_logs = cpu_logger.process_log()
    trace_paths = [join(build_trace_path, f) for f in os.listdir(build_trace_path) if f.endswith('trace')]
    for trace_path in trace_paths:
        if time_cutoff and os.path.getmtime(trace_path) < time_cutoff:
            continue
        with open(trace_path, 'r') as trace_file:
            traces = json.load(trace_file)
            new_traces = CPULog.apply_log_to_trace(cpu_logs, traces)
        with open(trace_path + '.json', 'w') as new_trace_file:
            json.dump(new_traces, new_trace_file)
