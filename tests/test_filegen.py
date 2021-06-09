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

import unittest

from uberpoet.filegen import (FileResult, FuncType, Language, get_func_call_template, get_import_func_calls,
                              objc_to_objc_func_call_template, objc_to_swift_func_call_template,
                              swift_to_objc_friendly_func_call_template, swift_to_objc_func_call_template,
                              swift_to_swift_func_call_template, swift_to_swift_objc_friendly_func_call_template)


class TestFileGen(unittest.TestCase):

    def test_func_call_template(self):
        # From Swift to ObjC all method calls can be invoked.
        self.assertEqual(get_func_call_template(Language.SWIFT, Language.SWIFT, FuncType.SWIFT_ONLY),
                         swift_to_swift_func_call_template)
        self.assertEqual(get_func_call_template(Language.SWIFT, Language.OBJC, FuncType.SWIFT_ONLY),
                         swift_to_objc_func_call_template)
        self.assertEqual(get_func_call_template(Language.SWIFT, Language.SWIFT, FuncType.OBJC_FRIENDLY),
                         swift_to_swift_objc_friendly_func_call_template)
        self.assertEqual(get_func_call_template(Language.SWIFT, Language.OBJC, FuncType.OBJC_FRIENDLY),
                         swift_to_objc_friendly_func_call_template)

        # From ObjC to Swift we cannot invoke methods that are only available to Swift.
        with self.assertRaises(ValueError):
            get_func_call_template(Language.OBJC, Language.SWIFT, FuncType.SWIFT_ONLY)
            get_func_call_template(Language.OBJC, Language.OBJC, FuncType.SWIFT_ONLY)

        # From ObjC to Swift with ObjC friendly methods
        self.assertEqual(get_func_call_template(Language.OBJC, Language.SWIFT, FuncType.OBJC_FRIENDLY),
                         objc_to_swift_func_call_template)
        self.assertEqual(get_func_call_template(Language.OBJC, Language.OBJC, FuncType.OBJC_FRIENDLY),
                         objc_to_objc_func_call_template)

    def test_import_func_calls_swift(self):
        expected_swift_func_calls = """MyClass0().complexCrap0(arg: 4, stuff: 2)
MyClass0().complexCrap1(arg: 4, stuff: 2)
MyClass0().complexCrap2(arg: 4, stuff: 2)
MyClass0().complexStuff0(arg: "4")"""
        swift_import = self._create_import('MockLib0', Language.SWIFT)
        self.assertEqual(get_import_func_calls(Language.SWIFT, [swift_import]), expected_swift_func_calls)

    def test_import_func_calls_objc(self):
        expected_objc_func_calls = """[[[MyClass_0 alloc] init] complexCrap0:4 stuff:@"2"];
[[[MyClass_0 alloc] init] complexCrap1:4 stuff:@"2"];
[[[MyClass_0 alloc] init] complexCrap2:4 stuff:@"2"];"""
        objc_import = self._create_import('MockLib0', Language.OBJC)
        self.assertEqual(get_import_func_calls(Language.OBJC, [objc_import]), expected_objc_func_calls)

    def test_import_func_calls_for_str(self):
        self.assertEqual(get_import_func_calls(Language.SWIFT, ['File.h']), '')

    def _create_import(self, name, language):
        file_name = 'File0.swift' if language == Language.SWIFT else 'File0.m'
        if language == Language.SWIFT:
            class_functions = {FuncType.SWIFT_ONLY: [0, 1, 2], FuncType.OBJC_FRIENDLY: [0]}
        elif language == Language.OBJC:
            class_functions = {FuncType.OBJC_FRIENDLY: [0, 1, 2]}
        file_result = FileResult('body', [], {0: class_functions})
        return {name: {'files': {file_name: file_result}, 'loc': 150, 'language': language}}
