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

import logging
import tempfile
from math import ceil
from os.path import join

from .commandlineutil import count_loc
from .filegen import Language
from .memoize import memoized


class LOCCalculator(object):

    @memoized
    def calculate_loc(self, text, language):
        # actual code = lines of code, minus whitespace
        # calculated using cloc
        if language == Language.SWIFT:
            extension = '.swift'
        elif language == Language.OBJC:
            extension = '.m'
        else:
            raise ValueError("Unknown language: {}".format(language))

        tmp_file_path = join(tempfile.gettempdir(), 'ub_mock_gen_example_file{}'.format(extension))
        with open(tmp_file_path, 'w') as f:
            f.write(text)
        loc = count_loc(tmp_file_path, language)

        if loc == -1:
            logging.warning("Using fallback loc calc method due to cloc not being installed.")
            if language == Language.SWIFT:
                # fallback if cloc is not installed
                # this fallback is based on running cloc on the file made by `self.swift_gen.gen_file(3, 3)`
                # and saving the result of cloc(file_result.text) / file_result.text_line_count to here:
                fallback_code_multiplier = 0.811537333
            elif language == Language.OBJC:
                # fallback if cloc is not installed
                # this fallback is based on running cloc on the file made by `self.objc_source_gen.gen_file(3, 3)`
                # and saving the result of cloc(file_result.text) / file_result.text_line_count to here:
                fallback_code_multiplier = 0.772727272
            else:
                raise ValueError('No fallback multiplier calculated for language: {}'.format(language))

            loc = int(ceil(len(text.split('\n')) * fallback_code_multiplier))

        return loc
