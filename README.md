# Uber Poet

[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/2983/badge)](https://bestpractices.coreinfrastructure.org/projects/2983)
[![Build Status](https://github.com/uber/uber-poet/actions/workflows/python-app.yml/badge.svg)](https://github.com/uber/uber-poet/actions)

This python app makes mock Xcode Swift / ObjC app projects with [Buck](https://buckbuild.com/), [Bazel](https://bazel.build/)
and [CocoaPods](https://cocoapods.org).  It lets us test different Swift / ObjC module configurations to see how much build speed is affected by different [dependency graphs](docs/layer_types.md) with identical amounts of code.  There are two main command line apps:

* `genproj.py` which generates one app which you have to build manually yourself.  Either with `buck`, `bazel` or `xcodebuild`.
* `multisuite.py`, which generates all module configs, builds them, records how long they take to build into a CSV and outputs it's results to a directory passed in the command line.  Essentially a benchmark test suite.  Can take several hours to run depending how many lines of code each app takes.

This app was architected so other languages, graph generators or build systems wouldn't be much work to add.  Theoretically you could extend this app to generate java gradle android apps with the same [dependency graph types](docs/layer_types.md).

## How to Install / Dependencies

With a mac computer that can run macOS 10.13+, install all the dependencies below:

* macOS 10.13.X+, untested on older versions.
* Python 2.7.X (pre-installed on macOS 10.13+)
* Xcode command line tools & Xcode
    * Install with: `xcode-select --install` / [The mac app store](https://itunes.apple.com/us/app/xcode/id497799835)
* [pipenv](https://pipenv.readthedocs.io/en/latest/)
    * Install with [homebrew](https://brew.sh): `brew install pipenv`
* Optional:  [cloc (Count Lines Of Code)](https://github.com/AlDanial/cloc)
    * Install with [homebrew](https://brew.sh): `brew install cloc`

Depending on which project generator you plan to use, you will need to install at least one of the following:

* [Buck](https://buckbuild.com/)
    * [Install instructions](https://buckbuild.com/setup/getting_started.html)
* [Bazel](https://bazel.build/)
    * [Install instructions](https://docs.bazel.build/bazel-overview.html)
* [CocoaPods](https://cocoapods.org/)
    * [Install instructions](https://cocoapods.org/#get_started)

Then:

* Download / git clone this project into a folder.
* Run `pipenv install` to install the required python dependencies.
* If you want to run unit tests or develop for this app, make sure to run `pipenv install --dev`

## How to Use

After installing all required dependencies:

See `pipenv run ./genproj.py -h` or `pipenv run ./mulisuite.py -h` for general help.  Also take a look at the shell scripts in [examples/](examples/) to see examples on how to use these command line programs.

Here a few quick examples:

Generate a project using Buck:
```bash
pipenv run ./genproj.py --output_directory "$HOME/Desktop/mockapp" \
                        --project_generator_type "buck" \
                        --blaze_module_path "/mockapp" \
                        --gen_type flat \
                        --swift_lines_of_code 150000
```

Generate a project using Bazel:
```bash
pipenv run ./genproj.py --output_directory "$HOME/Desktop/mockapp" \
                        --project_generator_type "bazel" \
                        --blaze_module_path "/mockapp" \
                        --gen_type flat \
                        --swift_lines_of_code 150000
```

Generate a project using CocoaPods:
```bash
pipenv run ./genproj.py --output_directory "$HOME/Desktop/mockapp" \
                        --project_generator_type "cocoapods" \
                        --gen_type flat \
                        --swift_lines_of_code 150000
```

You may also generate a project that includes both Swift and ObjC:

```bash
pipenv run ./genproj.py --output_directory "$HOME/Desktop/mockapp" \
                        --project_generator_type "cocoapods" \
                        --gen_type flat \
                        --swift_lines_of_code 100000 \
                        --objc_lines_of_code 50000
```

```bash
# You usually want to use `caffeinate` to prevent your computer 
# from going to sleep during a multi hour build test suite.             
caffeinate -s pipenv run \
./multisuite.py --log_dir "$HOME/Desktop/multisuite_build_results" \
                --app_gen_output_dir "$HOME/Desktop/multisuite_build_results/app_gen"
```

You may also generate a project that matches your own project's dependency graph by using `--gen_type dot` parameter as well as supplying the location of the [`dot` file](https://en.wikipedia.org/wiki/DOT_(graph_description_language)) that represents the graph:

```bash
pipenv run ./genproj.py --output_directory "$HOME/Desktop/mockapp" \
                        --project_generator_type "cocoapods" \
                        --gen_type dot \
                        --dot_file_path "$HOME/MyProject/my_project_graph.dot" \
                        --dot_root_node_name "MyProject" \
                        --swift_lines_of_code 150000
```

Examples on how to generate a `dot` file:


Using Buck:
```
buck query \"deps(target)\" --dot > file.gv
```

Using Bazel:
```
bazel query "deps(target)" --output graph > graph.in
```

Using CocoaPods:

Install and use the [cocoapods-dependencies](https://github.com/segiddins/cocoapods-dependencies) plugin.

You may also supply an optional JSON file to be used as a LOC map.  This allows you to generate a project from your own dependency graph in which each generated module has proportional LOC to your original graph.

```bash
pipenv run ./genproj.py --output_directory "$HOME/Desktop/mockapp" \
                        --project_generator_type "cocoapods" \
                        --gen_type dot \
                        --dot_file_path "$HOME/MyProject/my_project_graph.dot" \
                        --dot_root_node_name "MyProject" \
                        --loc_json_file_path "$HOME/MyProject/cloc_mappings.json"
```

Please note the format of the JSON file for LOC mappings must look like:

```json
{
    "MyLibrary":500,
    "MyOtherLibrary":42
}
```

You may also specify a LOC mapping file that includes the language that you want to use for each module, for example:

```json
{
    "MyLibrary": { "loc": 500, "language": "Objective-C" },
    "MyOtherLibrary":42
}
```

NOTE: All nodes found in your `dot` file must be present in your JSON LOC mappings file.

Examples on how to get the CLOC:

```
cloc file.swift --include-lang="Swift" --json
```

Parse the JSON with your favorite language and read the `"code"` value from the `"SUM"` key.

## How to Contribute / Develop

Take a look at [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)! 

## Project Status

This project is stable and being incubated for long-term support.

## Licence

This project is covered by the Apache License, Version 2.0:

http://www.apache.org/licenses/LICENSE-2.0

[LICENSE.txt](LICENSE.txt)
