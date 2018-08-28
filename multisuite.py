#!/usr/bin/env python

import argparse
from mockappgen.commandline import CommandLineInterface

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build all mock app types and log times to a log file.')
    parser.add_argument('--log_dir', required=True,
                        help='Where logs such as build times should exist.')
    parser.add_argument('--git_root', required=True,
                        help='Where the ios monorepo checkout is.')
    parser.add_argument('--switch_xcode_versions', action='store_true',
                        help='Switch xcode verions as part of the full multisuite test. Requires sudo.')
    args = parser.parse_args()
    CommandLineInterface().multisuite(args.log_dir, args.git_root, args.switch_xcode_versions)
