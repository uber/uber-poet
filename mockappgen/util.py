import os
import subprocess
import distutils.spawn


class SeedContainer(object):
    seed = 0


def seed():
    SeedContainer.seed += 1
    return SeedContainer.seed


def first_in_dict(d):
    if len(d) > 0:
        k = d.keys()[0]
        return d[k]
    return None


def first_key(d):
    return d.keys()[0]


def makedir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def merge_lists(two_d_list):
    # I know this is a fold / reduce, but I got an error when I tried
    # the reduce function?
    return [i for li in two_d_list for i in li]


def parse_xcode_version():
    version_out = subprocess.check_output(['xcodebuild', '-version']).splitlines()
    version_num = version_out[0].split(' ')[1]
    build_id = version_out[1].split(' ')[2]
    return version_num, build_id


def sudo_enabled():
    try:
        subprocess.check_call(['sudo', '-n', 'true'])
        return True
    except subprocess.CalledProcessError:
        return False


def check_dependent_commands(command_list):
    missing_commands = []
    for command in command_list:
        if not distutils.spawn.find_executable(command):
            missing_commands.append(command)
    return missing_commands
