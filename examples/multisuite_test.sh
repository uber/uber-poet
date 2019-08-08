#!/bin/bash

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

set -xe

GIT_ROOT="$(git rev-parse --show-toplevel)"

pipenv install

# You usually want to use `caffeinate` to prevent your computer from going to sleep during
# a multi hour build test suite.
caffeinate -s pipenv run $GIT_ROOT/multisuite.py \
--log_dir "$HOME/Desktop/multisuite_build_results" \
--app_gen_output_dir "$HOME/Desktop/multisuite_build_results/app_gen" \
--test_build_only \
"$@"


# Uncomment this if you use --trace_cpu:
# TODO figure out a better way to catch dangling top processes if there is a crash / error in the main program
# echo "Killing potential dangling top subprocesses from CPULog"
# sudo killall top
