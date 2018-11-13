#!/bin/bash

set -xe

GIT_ROOT="$(git rev-parse --show-toplevel)"
APP_GEN="$GIT_ROOT/multisuite.py"

# You usually want to use `caffeinate` to prevent your computer from going to sleep during
# a multi hour build test suite.
caffeinate -s "$APP_GEN" \
--log_dir "$HOME/Desktop/multisuite_build_results" \
--app_gen_output_dir "$HOME/Desktop/multisuite_build_results/app_gen" \
--test_build_only \
"$@"


# TODO figure out a better way to catch dangling top processes if there is a crash / error in the main program
echo "Killing potential dangling top subprocesses from CPULog"
sudo killall top
