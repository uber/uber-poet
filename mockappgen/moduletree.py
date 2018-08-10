import random


def merge_arrays(two_d_array):
    # I know this is a fold / reduce, but I got an error when I tried
    # the reduce function?
    out = []
    for array in two_d_array:
        out += array
    return out


class ModuleNode(object):
    """Represents a module in a dependency graph"""

    APP = 'APP'
    LIBRARY = 'LIBRARY'

    def __init__(self, name, node_type, deps=[]):
        super(ModuleNode, self).__init__()
        self.name = name
        self.node_type = node_type  # app or library
        self.deps = deps
        self.extra_info = None  # useful for file indexes and such

    def __hash__(self):
        return hash((self.name, self.node_type))

    def __eq__(self, other):
        return (self.name, self.node_type) == (other.name, other.node_type)

    def __repr__(self):
        return "ModuleNode('{}','{}')".format(self.name, self.node_type)

    def __str__(self):
        extra = True if self.extra_info else False
        return "<{} : {} deps: {} info: {}>".format(self.name, self.node_type, len(self.deps), extra)

    @staticmethod
    def gen_layered_graph(layer_count, nodes_per_layer, deps_per_node=5):
        """Generates a module dependency graph that has `layer_count` layers,
        with each module only depending on a random selection of the modules
        below it"""

        def node(layer, node):
            return ModuleNode('MockLib{}_{}'.format(layer, node), ModuleNode.LIBRARY)
        layers = [[node(l, n) for n in xrange(nodes_per_layer)] for l in xrange(layer_count)]
        all_nodes = merge_arrays(layers)
        app_node = ModuleNode('App', ModuleNode.APP, layers[0])

        for i, layer in enumerate(layers):
            lower_layers = layers[(i + 1):] if i != len(layers) - 1 else []
            lower_merged = merge_arrays(lower_layers)
            for node in layer:
                if deps_per_node < len(lower_merged):
                    node.deps = random.sample(lower_merged, deps_per_node)
                else:
                    node.deps = lower_merged

        return app_node, (all_nodes + [app_node])

    @staticmethod
    def gen_flat_graph(module_count):
        """Generates a module dependency graph that depends on `module_count`
        libraries that don't depend on anything"""
        libraries = [ModuleNode('MockLib{}'.format(i), ModuleNode.LIBRARY) for i in xrange(module_count)]
        app_node = ModuleNode('App', ModuleNode.APP, libraries)

        return app_node, (libraries + [app_node])
