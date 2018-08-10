import os

from filegen import SwiftFileGenerator
from util import first_in_dict, first_key, makedir


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

# Generation Functions

    def gen_app(self, module_count=20):
        app_module_dir = os.path.join(self.app_root, "App")
        makedir(app_module_dir)

        module_index = self.gen_modules(module_count)

        app_files = {
            "Info.plist": self.load_resource("Info.plist"),  # TODO do a straight copy operation instead
            "main.swift": self.gen_app_main(module_index),
            "BUCK": self.gen_app_buck(module_index),
        }

        for name, text in app_files.iteritems():
            self.write_file(os.path.join(app_module_dir, name), text)

    def gen_app_buck(self, module_index):
        keys = module_index.keys()
        module_dep_list = self.make_list_str(["'{0}/{1}:{1}'".format(self.buck_app_root, i) for i in keys])
        module_scheme_list = self.make_list_str(
            ["'{1}': '{0}/{1}:{1}Scheme'".format(self.buck_app_root, i) for i in keys])
        return self.bzl_app_template.format(module_scheme_list, module_dep_list)

    def gen_app_main(self, module_index):
        chosen_main_module = first_key(module_index)
        file_index = first_in_dict(first_in_dict(module_index))
        class_key = first_key(file_index.classes)
        class_index = first_in_dict(file_index.classes)
        function_key = class_index[0]
        return self.swift_gen.gen_main(chosen_main_module, class_key, function_key)

    def gen_modules(self, module_count):
        module_index = {}
        for i in xrange(module_count):
            name, index = self.gen_module(i)  # also writes modules to disk as a side effect
            module_index[name] = index
        return module_index

    def gen_module(self, lib_index):
        # Make BUCK Text
        module_name = "MockLib{}".format(lib_index)
        buck_text = self.bzl_lib_template.format(module_name, "")

        # Make Swift Text
        files = {"File{}.swift".format(i): self.swift_gen.gen_file(3, 3) for i in xrange(20)}

        # Make Module Directories
        module_dir_path = os.path.join(self.app_root, module_name)
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

        return module_name, files
