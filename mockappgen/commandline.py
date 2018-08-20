import argparse
import modulegen
import shutil
import os
import time
import dotreader
import moduletree


class CommandLineInterface(object):
    def __init__(self):
        super(CommandLineInterface, self).__init__()

    def make_args(self):
        """Parses command line arguments"""
        arg_desc = 'Generate a fake test project with many buck modules'

        parser = argparse.ArgumentParser(description=arg_desc,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)

        parser.add_argument('-o', '--output_directory', required=True,
                            help='Where the mock project should be output.')
        parser.add_argument('-bmp', '--buck_module_path', required=True,
                            help='Where the mock project should be output.')
        parser.add_argument('-loc', '--total_lines_of_code', type=int, default=1500000,
                            help='How many approx lines of code should be generated.')

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-mc', '--module_count', type=int,
                           help='How many modules your fake app should contain')
        group.add_argument('-dot', '--dot_file',
                           help='Generate a project based on a dot file representation from a `buck query "deps(target)" --dot` output')

        # TODO implement this
        # TODO take layer count as an argument
        #  action='store_true'
        # parser.add_argument('-ll', '--lines_per_library', default=5000,
        #                     help='How many lines a mock "library" module should contain')
        # parser.add_argument('-la', '--lines_per_app_module', default=5000,
        #                     help='How many lines a mock "app" module should contain')
        # parser.add_argument('-ml', '--library_module_count', default=70,
        #                     help='How many library modules your fake app should contain')
        # parser.add_argument('-ma', '--app_module_count', default=150,
        #                     help='How many app modules your fake app should contain')

        return parser, parser.parse_args()

    def main(self):
        start = time.time()

        _, args = self.make_args()

        if os.path.isdir(args.output_directory):
            # TODO fix this quick overwrite hack, since we should warn/ask on overwrite
            print "Deleting old mock app directory", args.output_directory
            shutil.rmtree(args.output_directory)
        gen = modulegen.BuckProjectGenerator(args.output_directory, args.buck_module_path)

        app_node, node_list = None, None
        if args.dot_file:
            print "Reading dot file:", args.dot_file
            app_node, node_list = dotreader.DotFileReader().read_dot_file(args.dot_file)
        elif args.module_count:
            app_node, node_list = moduletree.ModuleNode.gen_layered_graph(10, args.module_count / 10)
        else:
            print "Unexpected argument set, aborting."
            raise ValueError("Invalid Arguments")  # TODO better error raising

        print "Creating a", len(node_list), "module count mock app in", args.output_directory
        print "Example command: $ ./monorepo project", "/{}/App:MockApp".format(args.buck_module_path)
        gen.gen_app(app_node, node_list, args.total_lines_of_code)

        fin = time.time()
        print "Done in", fin-start, "s"
