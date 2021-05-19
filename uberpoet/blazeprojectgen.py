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

import logging
import shutil
import tempfile
from os.path import basename, dirname, join

from . import locreader
from .commandlineutil import count_loc
from .filegen import SwiftFileGenerator
from .moduletree import ModuleNode
from .util import first_in_dict, first_key, makedir


class BlazeProjectGenerator(object):
    DIR_NAME = dirname(__file__)
    RESOURCE_DIR = join(DIR_NAME, "resources")

    def __init__(self, app_root, blaze_app_root, use_wmo=False, flavor='buck'):
        self.app_root = app_root
        self.blaze_app_root = blaze_app_root
        self.bzl_lib_template = self.load_resource("mock{}libtemplate.bzl".format(flavor))
        self.bzl_app_template = self.load_resource("mock{}apptemplate.bzl".format(flavor))
        self.swift_gen = SwiftFileGenerator()
        self.use_wmo = use_wmo
        self.flavor = flavor
        self.swift_file_size_loc = None
        self.calculate_loc()

    @property
    def wmo_state(self):
        return "YES" if self.use_wmo else "NO"

    def calculate_loc(self):
        # actual code = lines of code, minus whitespace
        # calculated using cloc
        file_result = self.swift_gen.gen_file(3, 3)
        tmp_file_path = join(tempfile.gettempdir(), 'ub_mock_gen_example_file.swift')
        with open(tmp_file_path, 'w') as f:
            f.write(file_result.text)
        self.swift_file_size_loc = count_loc(tmp_file_path)

        if self.swift_file_size_loc == -1:
            logging.warning("Using fallback loc calc method due to cloc not being installed.")
            # fallback if cloc is not installed
            # this fallback is based on running cloc on the file made by `self.swift_gen.gen_file(3, 3)`
            # and saving the result of cloc(file_result.text) / file_result.text_line_count to here:
            fallback_code_multiplier = 0.811537333

            self.swift_file_size_loc = int(file_result.text_line_count * fallback_code_multiplier)

    @staticmethod
    def load_resource(name):
        with open(join(BlazeProjectGenerator.RESOURCE_DIR, name), "r") as f:
            return f.read()

    @staticmethod
    def copy_resource(name, dest):
        origin = join(BlazeProjectGenerator.RESOURCE_DIR, name)
        shutil.copyfile(origin, dest)

    @staticmethod
    def copy_resource_dir(name, dest):
        origin = join(BlazeProjectGenerator.RESOURCE_DIR, name)
        shutil.copytree(origin, dest)

    @staticmethod
    def write_file(path, text):
        with open(path, "w") as f:
            f.write(text)

    @staticmethod
    def make_list_str(items):
        return (",\n" + (" " * 8)).join(items)

    def make_dep_list(self, items):
        return self.make_list_str(["'//{0}:{0}'".format(i) for i in items])

    def make_scheme_list(self, items):
        return self.make_list_str(
            ["{2: <20} :'/{0}/{1}:{1}Scheme'".format(self.blaze_app_root, i, "'{}'".format(i)) for i in items])

    def example_command(self):
        if self.flavor == 'buck':
            return "buck project //App:App"
        elif self.flavor == 'bazel':
            return "Use Tulsi or XCHammer to generate an Xcode project."

    # Generation Functions

    def gen_app(self, app_node, node_list, target_loc, loc_json_file_path):
        library_node_list = [n for n in node_list if n.node_type == ModuleNode.LIBRARY]

        if loc_json_file_path:
            loc_reader = locreader.LocFileReader()
            loc_reader.read_loc_file(loc_json_file_path)
            module_index = {
                n.name: self.gen_lib_module(n, loc_reader.loc_for_module(n.name)) for n in library_node_list
            }
        else:
            total_code_units = 0
            for l in library_node_list:
                total_code_units += l.code_units

            loc_per_unit = target_loc / total_code_units
            module_index = {n.name: self.gen_lib_module(n, loc_per_unit) for n in library_node_list}

        app_module_dir = join(self.app_root, "App")
        makedir(app_module_dir)

        app_build_file = "BUCK" if self.flavor == 'buck' else "BUILD"
        app_files = {
            "main.swift": self.gen_app_main(app_node, module_index),
            app_build_file: self.gen_app_build(app_node, library_node_list),
        }

        self.copy_resource("Info.plist", join(app_module_dir, "Info.plist"))

        if self.flavor == 'buck':
            self.copy_resource("mockbuckconfig", join(self.app_root, ".buckconfig"))
        elif self.flavor == 'bazel':
            self.copy_resource("mockbazelworkspace", join(self.app_root, "WORKSPACE"))
            self.copy_resource_dir("tools", join(self.app_root, "tools"))

        for name, text in app_files.iteritems():
            self.write_file(join(app_module_dir, name), text)

        if loc_json_file_path:
            # Copy the LOC file into the generated project.
            shutil.copyfile(loc_json_file_path, join(self.app_root, basename(loc_json_file_path)))

    def gen_app_build(self, node, all_nodes):
        module_dep_list = self.make_dep_list([i.name for i in node.deps])
        module_scheme_list = self.make_scheme_list([i.name for i in all_nodes])
        return self.bzl_app_template.format(module_scheme_list, module_dep_list, self.wmo_state)

    def gen_app_main(self, app_node, module_index):
        importing_module_name = app_node.deps[0].name
        file_index = first_in_dict(module_index[importing_module_name])
        class_key = first_key(file_index.classes)
        class_index = first_in_dict(file_index.classes)
        function_key = class_index[0]
        return self.swift_gen.gen_main(importing_module_name, class_key, function_key)

    # Library Generation

    def gen_lib_module(self, module_node, loc_per_unit):
        deps = self.make_dep_list([i.name for i in module_node.deps])
        build_text = self.bzl_lib_template.format(module_node.name, deps, self.wmo_state)

        # Make Swift Text
        file_count = (max(self.swift_file_size_loc, loc_per_unit) * module_node.code_units) / self.swift_file_size_loc
        if file_count < 1:
            raise ValueError("Lines of code count is too small for the module {} to fit one file, increase it.".format(
                module_node.name))
        files = {"File{}.swift".format(i): self.swift_gen.gen_file(3, 3) for i in xrange(file_count)}

        # Make Module Directories
        module_dir_path = join(self.app_root, module_node.name)
        files_dir_path = join(module_dir_path, "Sources")
        makedir(module_dir_path)
        makedir(files_dir_path)

        # Write BUCK or BUILD Files
        build_name = "BUCK" if self.flavor == 'buck' else "BUILD"
        build_path = join(module_dir_path, build_name)
        self.write_file(build_path, build_text)

        # Write Swift Files
        for file_name, file_obj in files.iteritems():
            file_path = join(files_dir_path, file_name)
            self.write_file(file_path, file_obj.text)
            file_obj.text = ""  # Save memory after write

        module_node.extra_info = files

        return files
