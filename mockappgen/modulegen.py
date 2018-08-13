import os

from filegen import SwiftFileGenerator
from util import first_in_dict, first_key, makedir
from moduletree import ModuleNode


class BuckProjectGenerator(object):
    DIR_NAME = os.path.dirname(__file__)
    RESOURCE_DIR = os.path.join(DIR_NAME, "resources")

    def __init__(self, app_root, buck_app_root):
        self.app_root = app_root
        self.buck_app_root = buck_app_root
        self.bzl_lib_template = self.load_resource("mocklibtemplate.bzl")
        self.bzl_app_template = self.load_resource("mockapptemplate.bzl")
        self.swift_gen = SwiftFileGenerator()

    def load_resource(self, name):
        with open(os.path.join(BuckProjectGenerator.RESOURCE_DIR, name), "r") as f:
            return f.read()

    def write_file(self, path, text):
        with open(path, "w") as f:
            f.write(text)

    def make_list_str(self, items):
        return (",\n" + (" " * 8)).join(items)

    def make_dep_list(self, items):
        return self.make_list_str(["'/{0}/{1}:{1}'".format(self.buck_app_root, i) for i in items])

    def make_scheme_list(self, items):
        return self.make_list_str(["{2: <20} :'/{0}/{1}:{1}Scheme'".format(self.buck_app_root, i, "'{}'".format(i)) for i in items])

    # Generation Functions

    def gen_app(self, module_count=90):
        layer_count = 10
        app_node, node_list = ModuleNode.gen_layered_graph(layer_count, module_count / layer_count)
        library_node_list = [n for n in node_list if n.node_type == ModuleNode.LIBRARY]
        module_index = {n.name: self.gen_lib_module(n) for n in library_node_list}

        app_module_dir = os.path.join(self.app_root, "App")
        makedir(app_module_dir)

        app_files = {
            "main.swift": self.gen_app_main(app_node, module_index),
            "Info.plist": self.load_resource("Info.plist"),  # TODO do a straight copy operation instead
            "BUCK": self.gen_app_buck(app_node, library_node_list),
        }

        for name, text in app_files.iteritems():
            self.write_file(os.path.join(app_module_dir, name), text)

    def gen_app_buck(self, node, all_nodes):
        module_dep_list = self.make_dep_list([i.name for i in node.deps])
        module_scheme_list = self.make_scheme_list([i.name for i in all_nodes])
        return self.bzl_app_template.format(module_scheme_list, module_dep_list)

    def gen_app_main(self, app_node, module_index):
        chosen_main_module_name = app_node.deps[0].name
        file_index = first_in_dict(module_index[chosen_main_module_name])
        class_key = first_key(file_index.classes)
        class_index = first_in_dict(file_index.classes)
        function_key = class_index[0]
        return self.swift_gen.gen_main(chosen_main_module_name, class_key, function_key)

    # Library Generation

    def gen_lib_module(self, module_node):
        # Make BUCK Text
        deps = self.make_dep_list([i.name for i in module_node.deps])
        buck_text = self.bzl_lib_template.format(module_node.name, deps)

        # Make Swift Text
        files = {"File{}.swift".format(i): self.swift_gen.gen_file(3, 3) for i in xrange(48)}

        # Make Module Directories
        module_dir_path = os.path.join(self.app_root, module_node.name)
        files_dir_path = os.path.join(module_dir_path, "Sources")
        makedir(module_dir_path)
        makedir(files_dir_path)

        # Write BUCK File
        buck_path = os.path.join(module_dir_path, "BUCK")
        self.write_file(buck_path, buck_text)

        # Write Swift Files
        for file_name, file_obj in files.iteritems():
            file_path = os.path.join(files_dir_path, file_name)
            self.write_file(file_path, file_obj.text)
            file_obj.text = ""  # Save memory after write

        module_node.extra_info = files

        return files
