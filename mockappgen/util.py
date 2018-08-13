import os


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
