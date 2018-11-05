import argparse
import logging
import time
import modulegen
import commandline
from moduletree import ModuleGenType


class GenProjCommandLine(object):

    def make_args(self):
        """Parses command line arguments"""
        arg_desc = 'Generate a fake test project with many buck modules'

        parser = argparse.ArgumentParser(description=arg_desc)

        parser.add_argument('-o', '--output_directory', required=True,
                            help='Where the mock project should be output.')
        parser.add_argument('-bmp', '--buck_module_path', required=True,
                            help='The root of the BUCK dependency path of the generated code.')

        parser.add_argument('-gt', '--gen_type', required=True, choices=ModuleGenType.enum_list(),
                            help='What kind of mock app generation you want.')

        commandline.AppGenerationConfig.add_app_gen_options(parser)
        args = parser.parse_args()
        commandline.AppGenerationConfig.validate_app_gen_options(args)

        return args

    def main(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')
        start = time.time()

        args = self.make_args()

        graph_config = commandline.AppGenerationConfig()
        graph_config.pull_from_args(args)
        app_node, node_list = commandline.gen_graph(args.gen_type, graph_config)

        commandline.del_old_output_dir(args.output_directory)
        gen = modulegen.BuckProjectGenerator(args.output_directory, args.buck_module_path)

        logging.info("Generation type: %s", args.gen_type)
        logging.info("Creating a {} module count mock app in {}".format(len(node_list), args.output_directory))
        logging.info("Example command to generate xcode workspace: $ buck project /{}/App:MockApp".format(args.buck_module_path))
        gen.gen_app(app_node, node_list, graph_config.lines_of_code)

        fin = time.time()
        logging.info("Done in %f s", fin-start)
