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

import os


def do_nothing(_):
    pass


def integration_test(func):
    if 'INTEGRATION' in os.environ:
        return func
    else:
        return do_nothing


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def write_file(path, text):
    with open(path, 'w') as f:
        f.write(text)
