# Pear Poet

## Description

This python program makes a mock swift app project with BUCK.  It lets us test different module configurations to see how much build speed is effected by different dependency graphs with identical amounts of code.  There are two main apps:

* `genproj.py` which generates one app which you have to build manually yourself.  Either with BUCK or xcodebuild.
* `multisuite.py`, which generates all module configs, builds them, records how long they take to build and outputs it's results to a directory passed in the command line

## How to Use

See `./genproj.py -h` or `./mulisuite.py -h` for general help.

## How to Develop

* Currently we use visual studio code
* pytest for testing

## Possible Future Improvements

* Add simulation enhancers if the the mock app isn't good enough in simulating the build speed of Uber's large apps.
  * Add chokepoint build modules, simulating something similar to some large modules in Uber's apps.
  * Make codegen actually call functions in other modules and inside the module.
  * Dot graph mode, using cloc's sqllite3 db:
    * Make Objective-C modules as part of the mock app generation to better simulate a mixed app
    * Query the sqllite3 db that cloc generates to make the mock modules the same size as the real app's modules
    * Afterwards modify the generated mock app to see what causes slowdowns or speedups.
  * Research what the poor points of the swift compiler is and sprinkle that into the codegen. Some ideas:
    * Large math expressions
    * Make the code gen classes overload the `+` operator everywhere per class to make the type checker go wild.
    * Reasearch more possiblities
  * Import apple libraries, use them.
  * Import third party libraries from the cocoapods repo, use them some how.
