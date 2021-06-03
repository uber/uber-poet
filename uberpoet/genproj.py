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
import json
import logging
import sys
import time
from os.path import join

from . import blazeprojectgen, commandlineutil, cpprojectgen
from .moduletree import ModuleGenType


class GenProjCommandLine(object):

    @staticmethod
    def make_args(args):
        """Parses command line arguments"""
        arg_desc = 'Generate a fake test project with many modules'

        parser = argparse.ArgumentParser(description=arg_desc)

        parser.add_argument('-o', '--output_directory', required=True, help='Where the mock project should be output.')
        parser.add_argument(
            '-pgt',
            '--project_generator_type',
            choices=['buck', 'bazel', 'cocoapods'],
            default='buck',
            required=False,
            help='The project generator type to use.  Supported types are Buck, Bazel and CocoaPods. Default is `buck`')
        parser.add_argument(
            '-bmp',
            '--blaze_module_path',
            help='The root of the Buck or Bazel dependency path of the generated code.  Only used if Buck or Bazel '
            'generator type is used.')
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
            help='Whether or not to use whole module optimization when building swift modules.')
        parser.add_argument(
            '-udl',
            '--use_dynamic_linking',
            default=False,
            help='Whether or not to generate a project in which the modules are dynamically linked.  By default all '
            'projects use static linking. This option is currently used only by the CocoaPods generator.')
        parser.add_argument(
            '--print_dependency_graph',
            default=False,
            help='If true, prints out the dependency edge list and exits instead of generating an application.')
        # CocoaPods specific options
        parser.add_argument(
            '--cocoapods_use_deterministic_uuids',
            default=True,
            help='Whether to use deterministic uuids within the CocoaPods generated project.  Defaults to `true`.')
        parser.add_argument(
            '--cocoapods_generate_multiple_pod_projects',
            default=False,
            help='Whether to generate multiple pods projects.  Defaults to `false`.')

        commandlineutil.AppGenerationConfig.add_app_gen_options(parser)
        args = parser.parse_args(args)
        commandlineutil.AppGenerationConfig.validate_app_gen_options(args)

        return args

    def main(self, args=None):
        if args is None:
            args = sys.argv[1:]

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
        gen = project_generator_for_arg(args)

        logging.info("Project Generator type: %s", args.project_generator_type)
        logging.info("Generation type: %s", args.gen_type)
        logging.info("Creating a {} module count mock app in {}".format(len(node_list), args.output_directory))
        logging.info("Example command to generate Xcode workspace: $ {}".format(gen.example_command()))

        gen.gen_app(app_node, node_list, graph_config.swift_lines_of_code, graph_config.objc_lines_of_code,
                    graph_config.loc_json_file_path)

        fin = time.time()
        logging.info("Done in %f s", fin - start)

        project_info = {
            "generator_type": args.project_generator_type,
            "graph_config": args.gen_type,
            "options": {
                "use_wmo": bool(args.use_wmo),
                "use_dynamic_linking": bool(args.use_dynamic_linking),
                "swift_lines_of_code": args.swift_lines_of_code,
                "objc_lines_of_code": args.objc_lines_of_code
            },
            "time_to_generate": fin - start
        }
        with open(join(args.output_directory, "project_info.json"), "w") as project_info_json_file:
            json.dump(project_info, project_info_json_file)


def print_nodes(node_list):
    edges = [(node.name, dep.name) for node in node_list for dep in node.deps]
    for edge in edges:
        print(edge[0], edge[1])


def project_generator_for_arg(args):
    if args.project_generator_type == 'buck' or args.project_generator_type == 'bazel':
        if not args.blaze_module_path:
            raise ValueError("Must supply --blaze_module_path when using the Buck or Bazel generators.")
        return blazeprojectgen.BlazeProjectGenerator(
            args.output_directory, args.blaze_module_path, use_wmo=args.use_wmo, flavor=args.project_generator_type)
    elif args.project_generator_type == 'cocoapods':
        return cpprojectgen.CocoaPodsProjectGenerator(
            args.output_directory,
            use_wmo=args.use_wmo,
            use_dynamic_linking=args.use_dynamic_linking,
            use_deterministic_uuids=args.cocoapods_use_deterministic_uuids,
            generate_multiple_pod_projects=args.cocoapods_generate_multiple_pod_projects)
    else:
        raise ValueError("Unknown project generator arg: " + str(args.project_generator_type))


def main():
    GenProjCommandLine().main()


if __name__ == '__main__':
    main()
