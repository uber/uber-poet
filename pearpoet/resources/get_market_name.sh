#!/bin/sh

defaults read "$HOME/Library/Preferences/com.apple.SystemProfiler.plist" 'CPU Names' | cut -sd '"' -f 4 | uniq
