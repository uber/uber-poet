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

import distutils.spawn
import math
import os
import subprocess


class SeedContainer(object):
    """Holds the seed number variable"""
    seed = 0


def bool_xor(a, b):
    """Python's ^ operator is a bitwise xor, so we need to make a boolean equivalent function."""
    return (a and not b) or (not a and b)


def seed():
    """Gives you a unique number for codegen ids"""
    SeedContainer.seed += 1
    return SeedContainer.seed


def first_in_dict(d):
    """Grabs the value returned by the first value in d.keys()"""
    if len(d) > 0:
        k = d.keys()[0]
        return d[k]
    return None


def first_key(dictionary_var):
    """dictionary_var.keys()[0]"""
    return dictionary_var.keys()[0]


def makedir(path):
    """Does a mkdir -p `path` if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)


def merge_lists(two_d_list):
    """Merges a 2d array into a 1d array. Ex: [[1,2],[3,4]] becomes [1,2,3,4]"""
    # I know this is a fold / reduce, but I got an error when I tried
    # the reduce function?
    return [i for li in two_d_list for i in li]


def percentage_split(list_to_split, percentages):
    """Splits an array based on the percentages provided."""
    result = []
    previous_index = 0
    for percentage in percentages:
        next_index = int(previous_index + math.ceil((len(list_to_split) * percentage)))
        result.append(list_to_split[previous_index:next_index])
        previous_index = next_index

    return result


def sudo_enabled():
    """Tells you if the current 'shell' has sudo permission."""
    try:
        subprocess.check_call(['sudo', '-n', 'true'])
        return True
    except subprocess.CalledProcessError:
        return False


def check_dependent_commands(command_list):
    """
    Checks if the commands are accessible by the process.
    Returns a list of misssing commands.  Empty if all commands are available.
    """
    # noinspection PyUnresolvedReferences
    return [command for command in command_list if not distutils.spawn.find_executable(command)]


def pad_list(l, size, value=0):
    """Pads the right side of the list `l` to `size` if len(l) is less than size with `value`."""
    if len(l) >= size:
        return l

    return l + ([value] * (size - len(l)))


def grab_mac_marketing_name():
    """
    Returns a string telling you you the macOS marketing name of the device your running on.
    Ex: "MacBook Pro (15-inch, 2018)"
    """
    script_path = os.path.join(os.path.dirname(__file__), "resources", "get_market_name.sh")
    return subprocess.check_output([script_path])
