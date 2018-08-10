import argparse
import modulegen
import shutil


class CommandLineInterface(object):
    def __init__(self):
        super(CommandLineInterface, self).__init__()

    def make_args(self):
        """Parses command line arguments"""
        arg_desc = 'Generate a fake test project with many buck modules'

        parser = argparse.ArgumentParser(description=arg_desc,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)

        parser.add_argument('-o', '--output_directory', default='/tmp/ub_mock_project',
                            help='Where the mock project should be output.')
        parser.add_argument('-bmp', '--buck_module_path', default='/apps/mockapp',
                            help='Where the mock project should be output.')
        parser.add_argument('-mc', '--module_count', default=150,
                            help='How many modules your fake app should contain')

        # TODO implement this
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
        parser, args = self.make_args()
        print "Creating a", args.module_count, "module count mock app in", args.output_directory
        shutil.rmtree(args.output_directory)  # TODO fix this
        gen = modulegen.BuckProjectGenerator(args.output_directory, args.buck_module_path)
        gen.gen_app(args.module_count)
        print "Done"
