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

        app_node, node_list = commandline.gen_graph(args.gen_type, dot_path, module_count)

        commandline.del_old_output_dir(args.output_directory)
        gen = modulegen.BuckProjectGenerator(args.output_directory, args.buck_module_path)

        logging.info("Creating a {} module count mock app in {}".format(len(node_list), args.output_directory))
        logging.info("Example command: $ ./monorepo project /{}/App:MockApp".format(args.buck_module_path))
        gen.gen_app(app_node, node_list, args.total_lines_of_code)

        fin = time.time()
        logging.info("Done in %f s", fin-start)
