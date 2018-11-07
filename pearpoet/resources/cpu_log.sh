#!/bin/bash

date_fn () {
  while read -r LINE
  do
    echo "$(date +%s) $LINE"
  done
}

# This isn't a perfect way to track cpu usage.  
# You'll notice some skew in terms of a second or two, 
# but it works well enough for our usecase of 700-1500s builds.

top -l 0 -n 0 | grep --line-buffered CPU | date_fn