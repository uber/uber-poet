#  Copyright (c) 2018 Uber Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="uberpoet",
    version="1.0.0",
    license='Apache License, Version 2.0',
    author="Uber Technologies, Inc.",
    description="A mock swift project generator & build runner to help benchmark various module configurations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/uber/uber-poet",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: MacOS X",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
    ],
    entry_points={
        'console_scripts': [
            'uberpoet-genproj.py=uberpoet.genproj:main',
            'uberpoet-multisuite.py=uberpoet.multisuite:main',
        ],
    },
)
