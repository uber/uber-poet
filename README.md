# Pear Poet

## Description

This python module makes mock Xcode swift app projects with BUCK.  It lets us test different swift module configurations to see how much build speed is affected by different dependency graphs with identical amounts of code.  There are two main command line apps:

* `genproj.py` which generates one app which you have to build manually yourself.  Either with BUCK or xcodebuild.
* `multisuite.py`, which generates all module configs, builds them, records how long they take to build and outputs it's results to a directory passed in the command line


## How to Install / Dependencies

With a mac computer that can run macOS 10.13+, install all the dependencies below:

* macOS 10.13.X+, untested on older versions.
* Python 2.7.X (pre-installed on macOS 10.13+)
* Xcode command line tools & Xcode
   * Install with: `xcode-select --install` / [The mac app store](https://itunes.apple.com/us/app/xcode/id497799835)
* [BUCK for xcode project generation](https://buckbuild.com/)
	* [Install instructions](https://buckbuild.com/setup/getting_started.html)
* Optional:  [cloc (Count Lines Of Code)](https://github.com/AlDanial/cloc)
   * Install with [homebrew](https://brew.sh): `brew install cloc`

Then download this project into a folder and run `genproj.py` or `multisuite.py` via the Terminal app.

## How to Use

See `./genproj.py -h` or `./mulisuite.py -h` for general help.  Also take a look at the shell scripts in `examples/shell_scripts` to see examples on how to use these command line programs.

## How we Develop

* Currently we use [Visual Studio Code](https://code.visualstudio.com)
	* Look at `examples/dev_config` for recommended configurations.
	* Just open this directory in vscode (Ex: `code pear-poet`) to start developing!
* pytest for testing

## Possible Future Improvements

* Add simulation enhancers if the the mock app isn't good enough in simulating the build speed of large applications.
  * Add chokepoint build modules, simulating something similar to some large modules in Uber's apps.
  * Make codegen actually call functions in other modules and inside the module.
  * Additions to dot graph mode, using cloc's sqllite3 db:
      * Make Objective-C modules as part of the mock app generation to better simulate a mixed app
      * Query the sqllite3 db that cloc generates to make the mock modules the same size as the real app's modules
      * Afterwards modify the generated mock app to see what causes slowdowns or speedups.
  * Research what the poor points of the swift compiler is and sprinkle that into the codegen. Some ideas:
      * Large math expressions
      * Make the code gen classes overload the `+` operator everywhere per class to make the type checker go wild.
      * Research more possibilities
  * Import apple libraries, use them.
  * Import third party libraries from the cocoapods repo, use them some how.

* Add more project config support:
  * Add swift project manager project descripition support to remove buck dependency.
  * Test / add bazel support to see if there is any difference between buck or bazel
  * (relatively a more work) add direct xcode project & workspace direction
