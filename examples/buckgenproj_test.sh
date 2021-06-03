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
GENPROJ_ROOT="$HOME/Desktop/buckgenproj_out"
BUILD_LOG_PATH="$GENPROJ_ROOT/mockapp_build_log.txt"
PROJECT_OUT="$GENPROJ_ROOT/mockapp"

xcodebuild -version
pipenv install

pipenv run $GIT_ROOT/genproj.py \
           --output_directory "$PROJECT_OUT" \
           --blaze_module_path "/mockapp" \
           --gen_type flat \
           --swift_lines_of_code 150000

MOCK_WORKSPACE_PATH="$PROJECT_OUT/App/App.xcworkspace"
cd "$PROJECT_OUT"
time buck build "//..." > "$BUILD_LOG_PATH"
