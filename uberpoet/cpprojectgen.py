#  Copyright (c) 2021 Uber Technologies, Inc.
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

import json
import math
import shutil
from os.path import basename, dirname, join

from . import locreader
from .filegen import Language, ObjCHeaderFileGenerator, ObjCSourceFileGenerator, SwiftFileGenerator
from .loccalc import LOCCalculator
from .moduletree import ModuleNode
from .util import first_in_dict, first_key, makedir


class CocoaPodsProjectGenerator(object):
    DIR_NAME = dirname(__file__)
    RESOURCE_DIR = join(DIR_NAME, "resources")

    def __init__(self,
                 app_root,
                 use_wmo=False,
                 use_dynamic_linking=False,
                 use_deterministic_uuids=True,
                 generate_multiple_pod_projects=False):
        self.app_root = app_root
        self.pod_lib_template = self.load_resource("mockcplibtemplate.podspec")
        self.pod_app_template = self.load_resource("mockcpapptemplate.podspec")
        self.podfile_template = self.load_resource("mockpodfile")
        self.app_delegate_template = self.load_resource("mockappdelegate")
        self.swift_gen = SwiftFileGenerator()
        self.objc_source_gen = ObjCSourceFileGenerator()
        self.objc_header_gen = ObjCHeaderFileGenerator()
        self.loc_calc = LOCCalculator()
        self.use_wmo = use_wmo
        self.use_dynamic_linking = use_dynamic_linking
        self.use_deterministic_uuids = use_deterministic_uuids
        self.generate_multiple_pod_projects = generate_multiple_pod_projects
        self.swift_file_size_loc = self.loc_calc.calculate_loc(
            self.swift_gen.gen_file(3, 3).text, self.swift_gen.language())
        self.objc_file_size_loc = self.loc_calc.calculate_loc(
            self.objc_source_gen.gen_file(3, 3).text, self.objc_source_gen.language())

    @property
    def wmo_state(self):
        return "YES" if self.use_wmo else "NO"

    @staticmethod
    def load_resource(name):
        with open(join(CocoaPodsProjectGenerator.RESOURCE_DIR, name), "r") as f:
            return f.read()

    @staticmethod
    def copy_resource(name, dest):
        origin = join(CocoaPodsProjectGenerator.RESOURCE_DIR, name)
        shutil.copyfile(origin, dest)

    @staticmethod
    def write_file(path, text):
        with open(path, "w") as f:
            f.write(text)

    @staticmethod
    def make_list_str(items, padding=8):
        return ("\n" + (" " * padding)).join(items)

    def make_dep_list(self, items):
        return self.make_list_str(["s.dependency '{0}'".format(i) for i in items])

    def make_podfile_dep_list(self, items):
        return self.make_list_str(["pod '{0}', :path => '{0}/{0}.podspec'".format(i) for i in items], 4)

    def example_command(self):
        return "pod install"

    # Generation Functions

    def gen_app(self, app_node, node_list, target_swift_loc, target_objc_loc, loc_json_file_path):
        library_node_list = [n for n in node_list if n.node_type == ModuleNode.LIBRARY]

        if loc_json_file_path:
            loc_reader = locreader.LocFileReader()
            loc_reader.read_loc_file(loc_json_file_path)
            module_index = {}
            for n in library_node_list:
                loc = loc_reader.loc_for_module(n.name)
                language = loc_reader.language_for_module(n.name)
                module_index[n.name] = {
                    "files": self.gen_lib_module(module_index, n, loc, language),
                    "loc": loc,
                    "language": language
                }
        else:
            total_code_units = 0
            for l in library_node_list:
                total_code_units += l.code_units

            total_loc = target_swift_loc + target_objc_loc
            swift_module_count_percentage = round(float(target_swift_loc) / total_loc, 2)
            loc_per_unit = total_loc / total_code_units

            module_index = {}
            max_swift_index = int(math.ceil((len(library_node_list) * swift_module_count_percentage)))
            for idx, n in enumerate(library_node_list):
                language = Language.OBJC if idx >= max_swift_index else Language.SWIFT
                module_index[n.name] = {
                    "files": self.gen_lib_module(module_index, n, loc_per_unit, language),
                    "loc": loc_per_unit,
                    "language": language
                }

        app_module_dir = join(self.app_root, "App")
        makedir(app_module_dir)

        app_files = {
            "AppDelegate.swift": self.gen_app_main(app_node, module_index),
            "dummy.swift": "",
            "AppContainer.podspec": self.gen_app_podspec(app_node),
        }

        self.copy_resource("Info.plist", join(app_module_dir, "Info.plist"))

        for name, text in app_files.iteritems():
            self.write_file(join(app_module_dir, name), text)

        if loc_json_file_path:
            # Copy the LOC file into the generated project.
            shutil.copyfile(loc_json_file_path, join(self.app_root, basename(loc_json_file_path)))

        podfile_text = self.gen_podfile(library_node_list)
        podfile_path = join(self.app_root, "Podfile")
        self.write_file(podfile_path, podfile_text)

        serializable_module_index = {
            key: {
                "file_count": len(value["files"]),
                "loc": value["loc"]
            } for key, value in module_index.items()
        }

        with open(join(self.app_root, "module_index.json"), "w") as module_index_json_file:
            json.dump(serializable_module_index, module_index_json_file)

    def gen_app_podspec(self, node):
        module_dep_list = self.make_dep_list([i.name for i in node.deps])
        return self.pod_app_template.format(module_dep_list, self.wmo_state)

    def gen_app_main(self, app_node, module_index):
        importing_module_name = app_node.deps[0].name
        file_index = first_in_dict(module_index[importing_module_name]["files"])
        language = module_index[importing_module_name]["language"]
        class_key = first_key(file_index.classes)
        class_index = first_in_dict(file_index.classes)
        function_key = first_in_dict(class_index)[0]
        return self.swift_gen.gen_main(self.app_delegate_template, importing_module_name, class_key, function_key,
                                       language)

    # Library Generation

    def gen_lib_module(self, module_index, module_node, loc_per_unit, language):
        # Make Podspec Text
        deps = self.make_dep_list([i.name for i in module_node.deps])
        pod_text = self.pod_lib_template.format(module_node.name, deps, self.wmo_state)
        # We now return a topologically sorted list of the graph which means that we will already have the
        # deps of a module inside the module index before we process this one.  This allows us to reach into
        # the generated sources for the dependencies in order to create an instance of their class and
        # invoke their functions.
        deps_from_index = [{n.name: module_index[n.name]} for n in module_node.deps]

        # Make Text
        if language == Language.SWIFT:
            file_count = (
                max(self.swift_file_size_loc, loc_per_unit) * module_node.code_units) / self.swift_file_size_loc
            if file_count < 1:
                raise ValueError(
                    "Lines of code count is too small for the module {} to fit one file, increase it.".format(
                        module_node.name))
            files = {
                "File{}.swift".format(i): self.swift_gen.gen_file(3, 3, deps_from_index) for i in xrange(file_count)
            }
        elif language == Language.OBJC:
            file_count = (max(self.objc_file_size_loc, loc_per_unit) * module_node.code_units) / self.objc_file_size_loc
            if file_count < 1:
                raise ValueError(
                    "Lines of code count is too small for the module {} to fit one file, increase it.".format(
                        module_node.name))
            files = {}
            for i in xrange(file_count):
                objc_source_file = self.objc_source_gen.gen_file(
                    3, 3, import_list=deps_from_index + ['File{}.h'.format(i)])
                files["File{}.m".format(i)] = objc_source_file
                files["File{}.h".format(i)] = self.objc_header_gen.gen_file(objc_source_file)

        # Make Module Directories
        module_dir_path = join(self.app_root, module_node.name)
        files_dir_path = join(module_dir_path, "Sources")
        makedir(module_dir_path)
        makedir(files_dir_path)

        # Write podspec File
        pod_path = join(module_dir_path, "{0}.podspec".format(module_node.name))
        self.write_file(pod_path, pod_text)

        # Write Swift Files
        for file_name, file_obj in files.iteritems():
            file_path = join(files_dir_path, file_name)
            self.write_file(file_path, file_obj.text)
            file_obj.text = ""  # Save memory after write

        module_node.extra_info = files

        return files

    # Podfile Generation

    def gen_podfile(self, all_nodes):
        podfile_module_dep_list = self.make_podfile_dep_list([i.name for i in all_nodes])
        link_style = ":dynamic" if self.use_dynamic_linking else ":static"
        use_deterministic_uuids = str(self.use_deterministic_uuids).lower()
        generate_multiple_pod_projects = str(self.generate_multiple_pod_projects).lower()

        return self.podfile_template.format(
            "pod 'AppContainer', :path => 'App/AppContainer.podspec', :appspecs => ['App']", podfile_module_dep_list,
            link_style, use_deterministic_uuids, generate_multiple_pod_projects)
