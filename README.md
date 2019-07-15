# Uber Poet

[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/2983/badge)](https://bestpractices.coreinfrastructure.org/projects/2983)

This python app makes mock Xcode Swift app projects with [BUCK](https://buckbuild.com/).  It lets us test different swift module configurations to see how much build speed is affected by different [dependency graphs](docs/layer_types.md) with identical amounts of code.  There are two main command line apps:

* `genproj.py` which generates one app which you have to build manually yourself.  Either with BUCK or `xcodebuild`.
* `multisuite.py`, which generates all module configs, builds them, records how long they take to build into a CSV and outputs it's results to a directory passed in the command line.  Essentially a benchmark test suite.  Can take several hours to run depending how many lines of code each app takes.

This app was architected so other languages, graph generators or build systems wouldn't be much work to add.  Theoretically you could extend this app to generate java gradle android apps with the same [dependency graph types](docs/layer_types.md).

## Project Status

This project is stable and being incubated for long-term support.

## How to Install / Dependencies

With a mac computer that can run macOS 10.13+, install all the dependencies below:

* macOS 10.13.X+, untested on older versions.
* Python 2.7.X (pre-installed on macOS 10.13+)
* Xcode command line tools & Xcode
    * Install with: `xcode-select --install` / [The mac app store](https://itunes.apple.com/us/app/xcode/id497799835)
* [BUCK for xcode project generation](https://buckbuild.com/)
	* [Install instructions](https://buckbuild.com/setup/getting_started.html)
* [pipenv](https://pipenv.readthedocs.io/en/latest/)
    * Install with [homebrew](https://brew.sh): `brew install pipenv`
* Optional:  [cloc (Count Lines Of Code)](https://github.com/AlDanial/cloc)
    * Install with [homebrew](https://brew.sh): `brew install cloc`

Then download this project into a folder and run `genproj.py` or `multisuite.py` via the Terminal app.

## How to Use

See `./genproj.py -h` or `./mulisuite.py -h` for general help.  Also take a look at the shell scripts in [examples/](examples/) to see examples on how to use these command line programs.

Here a few quick examples:

```bash
pipenv run ./genproj.py --output_directory "$HOME/Desktop/mockapp" \
                        --buck_module_path "/mockapp" \
                        --gen_type flat \
                        --lines_of_code 150000
```

```bash
# You usually want to use `caffeinate` to prevent your computer 
# from going to sleep during a multi hour build test suite.             
caffeinate -s pipenv run \
./multisuite.py --log_dir "$HOME/Desktop/multisuite_build_results" \
                --app_gen_output_dir "$HOME/Desktop/multisuite_build_results/app_gen"
```

## How to Contribute / Develop

Take a look at [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)! 

## Licence

This project is covered by the Apache License, Version 2.0:

http://www.apache.org/licenses/LICENSE-2.0

[LICENSE.txt](LICENSE.txt)
