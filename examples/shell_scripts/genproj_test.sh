#!/bin/bash

set -xe

GIT_ROOT="$(git rev-parse --show-toplevel)"
APP_GEN="$GIT_ROOT/genproj.py"
GENPROJ_ROOT="$HOME/Desktop/genproj_out"
BUILD_LOG_PATH="$GENPROJ_ROOT/mockapp_build_log.txt"
PROJECT_OUT="$GENPROJ_ROOT/mockapp"

xcodebuild -version

$APP_GEN --output_directory "$PROJECT_OUT" \
         --buck_module_path "/mockapp" \
         --gen_type flat \
         --lines_of_code 150000

MOCK_WORKSPACE_PATH="$PROJECT_OUT/App/MockApp.xcworkspace"
cd "$GENPROJ_ROOT"
buck project "//mockapp/App:MockApp" -d
time xcodebuild build -scheme MockApp -sdk iphonesimulator -workspace "$MOCK_WORKSPACE_PATH" > "$BUILD_LOG_PATH"
