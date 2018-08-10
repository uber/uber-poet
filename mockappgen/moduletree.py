import operator
import random


class ModuleNode(object):
    """Represents a module in a dependency graph"""

    APP = 'APP'
    LIBRARY = 'LIBRARY'

    def __init__(self, name, node_type, deps=[]):
        super(ModuleNode, self).__init__()
        self.name = name
        self.node_type = node_type  # app or library
        self.deps = deps

    @staticmethod
    def gen_layered_graph(layer_count, nodes_per_layer, deps_per_node=5):
        """Generates a module dependency graph that has `layer_count` layers,
        with each module only depending on a random selection of the modules
        below it"""

        def node(layer, node):
            return ModuleNode('MockLib{}_{}'.format(layer, node), ModuleNode.LIBRARY)
        layers = [[node(l, n) for n in xrange(nodes_per_layer)] for l in xrange(layer_count)]

        for i, layer in enumerate(layers):
            lower_layers = layers[i + 1:] if i != len(layers) - 1 else []
            lower_merged = reduce(operator.add, lower_layers, 1)
            for node in layer:
                node.deps = random.sample(lower_merged, deps_per_node)

        return ModuleNode('App', ModuleNode.APP, layers[0])

    @staticmethod
    def gen_flat_graph(module_count):
        """Generates a module dependency graph that depends on `module_count`
        libraries that don't depend on anything"""
        libraries = [ModuleNode('MockLib{}'.format(i), ModuleNode.LIBRARY) for i in xrange(module_count)]
        return ModuleNode('App', ModuleNode.APP, libraries)
