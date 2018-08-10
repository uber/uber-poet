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
