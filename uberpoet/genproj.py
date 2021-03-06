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

import argparse
import logging
import sys
import time

from . import commandlineutil, projectgen
from .moduletree import ModuleGenType


class GenProjCommandLine(object):

    @staticmethod
    def make_args(args):
        """Parses command line arguments"""
        arg_desc = 'Generate a fake test project with many buck modules'

        parser = argparse.ArgumentParser(description=arg_desc)

        parser.add_argument('-o', '--output_directory', required=True, help='Where the mock project should be output.')
        parser.add_argument(
            '-bmp',
            '--buck_module_path',
            required=True,
            help='The root of the BUCK dependency path of the generated code.')

        parser.add_argument(
            '-gt',
            '--gen_type',
            required=True,
            choices=ModuleGenType.enum_list(),
            help='What kind of mock app generation you want.  See layer_types.md for a description of graph types.')
        parser.add_argument(
            '-wmo',
            '--use_wmo',
            default=False,
            help='Wether or not to use whole module optimization when building swift modules.')
        parser.add_argument(
            '--print_dependency_graph',
            default=False,
            help='If true, prints out the dependency edge list and exits instead of generating an application.')

        commandlineutil.AppGenerationConfig.add_app_gen_options(parser)
        args = parser.parse_args(args)
        commandlineutil.AppGenerationConfig.validate_app_gen_options(args)

        return args

    def main(self, args=sys.argv[1:]):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')
        start = time.time()

        args = self.make_args(args)

        graph_config = commandlineutil.AppGenerationConfig()
        graph_config.pull_from_args(args)
        app_node, node_list = commandlineutil.gen_graph(args.gen_type, graph_config)

        if args.print_dependency_graph:
            print_nodes(node_list)
            exit(0)

        commandlineutil.del_old_output_dir(args.output_directory)
        gen = projectgen.BuckProjectGenerator(args.output_directory, args.buck_module_path, use_wmo=args.use_wmo)

        logging.info("Generation type: %s", args.gen_type)
        logging.info("Creating a {} module count mock app in {}".format(len(node_list), args.output_directory))
        logging.info("Example command to generate xcode workspace: $ buck project /{}/App:MockApp".format(
            args.buck_module_path))
        gen.gen_app(app_node, node_list, graph_config.lines_of_code)

        fin = time.time()
        logging.info("Done in %f s", fin - start)


def print_nodes(node_list):
    edges = [(node.name, dep.name) for node in node_list for dep in node.deps]
    for edge in edges:
        print edge[0], edge[1]


def main():
    GenProjCommandLine().main()


if __name__ == '__main__':
    main()
