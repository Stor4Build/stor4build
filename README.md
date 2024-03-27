# Stor4Build Modeling Tool

[![PyPI - Version](https://img.shields.io/pypi/v/s4b.svg)](https://pypi.org/project/s4b)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/s4b.svg)](https://pypi.org/project/s4b)

-----

**Table of Contents**

- [Installation](#installation)
- [VS Code/Hatch Dev Environment](#vs_codehatch_dev_environment)
- [Web API Demo](#web_api_demo)
- [License](#license)

## Installation

```console
pip install s4b
```

## VS Code/Hatch Dev Environment

To set up a Visual Studio Code development environment, first install Python. Then install Visual Studio code and the Python extension(s) from Microsoft. Next, install hatch with

```console
pip install hatch
```

Clone the repository to the location of your choice and open the directory with Visual Studio Code. In the root folder of the repo, execute the following to generate an environment that has everything that is needed:

```console
hatch env create
```

To point Visual Studio Code at the created environment, find the environment with

```console
hatch run python -c "import sys;print(sys.executable)"
```

and copy the result. In Visual Studio Code, hit `ctrl-shift-P` to bring up the command palette, select "Python: Select Interpreter", and paste in the result from above. Any warnings (yellow squiqqly underlines) in the source files should go away. To make sure that everything has worked, run

```console
hatch shell
```

to enter the environment that was created, and then execute

```console
s4b-compute --help
```

You should see the help output from the tool.

## Web API Demo

A very simple flask-based web api demo is included. To launch the demo back end (that does the calculation) run

```console
s4b-api prototype --openstudio <openstudio/cli/path> -m <measures/path> --instance-path <path/to/run/in>
```

This will start up the flask **development** server in **debug** mode, and debugging output will appear on the console. Next, navigate a browser to 

```
http://127.0.0.1:5000/prototype
```

Make choices for the prototype, climate zone, and vintage, then click submit. Wait a few moments, and the page will change once the calculation is complete.

## License

`s4b` is distributed under the terms of the [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html) license.
