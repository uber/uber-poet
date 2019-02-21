# How to Contribute

Uber welcomes contributions of all kinds and sizes. This includes everything from from simple bug reports to large features.

Before we can accept your contributions, we kindly ask you to sign our [Contributor License Agreement](https://cla-assistant.io/uber/pear-poet).

## Workflow

We love GitHub issues!

For small feature requests, an issue first proposing it for discussion or demo implementation in a PR suffice.

For big features, please open an issue so that we can agree on the direction, and hopefully avoid investing a lot of time on a feature that might need reworking.

Small pull requests for things like typos, bug fixes, etc are always welcome.

## DOs and DON'Ts

* DO read this document to understand how Pear Poet is built and how we develop.
* DO write your change to conform to our formatting, lint, import sorting, etc tools before uploading your pull request.
* DO add types if possible with new and old code.  Types help with refactoring and are unit tests you don't have to write.
* DO include tests when adding new features. When fixing bugs, start with adding a test that highlights how the current behavior is broken.
* DO keep the discussions focused. When a new or related topic comes up it's often better to create new issue than to side track the discussion.
* DON'T submit PRs that alter licensing related files or headers. If you believe there's a problem with them, file an issue and we'll be happy to discuss it.

## How we Develop

* We used [Visual Studio Code](https://code.visualstudio.com) at first, but then moved to [pycharm](https://www.jetbrains.com/pycharm/) because of it's code inspector, richer refactoring tools and less configuration required to do basic things like testing.  You can use any code editor you would like, but please use PyCharm's [Inspect Code](https://www.jetbrains.com/help/pycharm/running-inspections.html) before you push.
* It's a goal to eventually move this code base to python 3, probably when python 2.7 won't be maintained anymore after 2020.

Tools used for managing the code base:
* pytest for running tests, basic unittest for writing tests
* yapf for formatting
* isort for sorting imports
* flake8 & pylint for linting
* PyCharm's "[Inspect Code](https://www.jetbrains.com/help/pycharm/running-inspections.html)" tool
* pipenv to manage application dependencies
* Tool configuration is kept in the `setup.cfg` file. Please use that as you develop.  

## Basic App Architecture

If you were to summarize Pear Poet as some python pseudocode:

```python
def make_project(config):
    abstract_dependency_graph = config.graph_generation_function(config.project_generation_options)
    swift_file_maker = SwiftFileGenerator()
    project_gen = BuckProjectGenerator(swift_file_maker)
    project_gen.generate_project_from(abstract_dependency_graph)
    project_gen.write_to_folder(config.output_path)
    
def multisuite(config):
    original_state = save_xcode_state()
    
    for xcode_config in config.xcode_configs:
        set_xcode_state(xcode_config)
        
        for gen_func in config.graph_generation_functions:
            proj_config = ProjectConfig(gen_func, join(config.output_path, gen_func.name)
            make_project(proj_config)
            
            trace = TimeAndCPUTracer().start()
            build_project(proj_config)
            trace.stop()
            
            trace.append_result_to_csv(config, proj_config)
            
    set_xcode_state(original_state)
```

![mock application generation code flow](images/project_gen.png)

Generating a mock app consists of 3 parts:

* Generating an abstract module dependency graph that represents the mock app. (`ModuleNode` in `moduletree.py`)
* Feeding this graph into a build description generator (ex: `BuckProjectGenerator` in `projectgen.py`), which creates project config files.
* And the build description generator using a file generator (ex `SwiftFileGenerator` in `filegen.py`) creating mock code files.
* And then writing all these files into a tree of folders

Most variation & configuration resides in the graph objects that the graph generation functions create.  So the if command line says there are 50 modules or 100 modules with a [`bs_layered`](docs/layer_types.md) graph type, that will show up in the generated abstract graph. 

`GenProjCommandLine` from `genproj.py` is the UI that the user's configuration for generating a mock app is passed into the above process.

`CommandLineMultisuite` from `multisuite.py`, does the same thing as `genproj.py`, but with a list of project generators, and builds these projects and records the build times.   It also gives you configuration options in how building is done.  Multisuite also uses code in `statementmanagement.py` & `cpulogger.py` to help it manage xcode build configuration and track CPU usage.

`dotreader.py` is used to generate dependency graphs from dot files.
