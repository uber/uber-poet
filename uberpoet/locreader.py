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
from typing import Dict, List, NoReturn, Set  # noqa: F401

from .filegen import Language


class LocFileReader(object):
    """
    This class reads a JSON file that includes the LOC information for each module and it supplies it to the
    project generator.
    """

    def __init__(self):
        self.cloc_mappings = None

    def read_loc_file(self, loc_file_path):
        # type: (str) -> NoReturn
        with open(loc_file_path, 'r') as f:
            self.cloc_mappings = json.load(f)

    def loc_for_module(self, mod_name):
        # type: (str) -> int
        if self.cloc_mappings is None:
            raise ValueError("Unable to provide LOC for module {}, no data is loaded yet!".format(mod_name))
        module_info = self.cloc_mappings[mod_name]
        return module_info["loc"] if type(module_info) is dict else module_info

    def language_for_module(self, mod_name):
        # type: (str) -> str
        if self.cloc_mappings is None:
            raise ValueError("Unable to provide LOC for module {}, no data is loaded yet!".format(mod_name))
        module_info = self.cloc_mappings[mod_name]
        return module_info["language"] if type(module_info) is dict else Language.SWIFT
