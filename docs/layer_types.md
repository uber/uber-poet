# Module Generation Graph Types

## flat
A module graph that has one app module which depends on one library layer of `module_count` modules.  Those modules do not depend on anything.

## bs_flat
A module graph that has one app module which depends on one library layer of modules.  Those modules do not depend on anything. Some of the modules in the library layer are 'big', the rest are small. There are `big_mod_count` number of big modules, and `small_mod_count` small modules.

## layered
A module graph of one app module and `layer_count` number of library layers. Each layer depends on a random selection of modules in lower layers. There are `module_count` number of library modules.

Due to probability a random selection of modules won't be built because they won't be connected to main module graph.

## bs_layered
A module graph that has one app module, one flat layer of `big_mod_count` big modules and 3 layers of `small_mod_count` modules under the big module layer which connect to random modules inside like the layed module graph type.

Due to probability a random selection of small modules won't be built because they won't be connected to main module graph.

## dot
Reads a dot file specified at `dot_file_path` which represents a dependency graph of code modules.  Picks `dot_root_node_name` as the app node to generate the app from.  You can generate a dot graph of your own buck app by using something like `buck query "deps(//apps/myapp:App)" --dot > file.gv`.  Every module in a dot graph mock app is the same size, unlike most applicaitons.