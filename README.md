# Stor4Build Modeling Tool

[![PyPI - Version](https://img.shields.io/pypi/v/stor4build.svg)](https://pypi.org/project/stor4build)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stor4build.svg)](https://pypi.org/project/stor4build)

-----

**Table of Contents**

- [Installation](#installation)
- [Command Line Usage](#command-line-usage)
- [VS Code/Hatch Dev Environment](#vs-codehatch-dev-environment)
- [Web API](#web-api)
- [License](#license)

## Installation

```console
pip install stor4build
```

## Command Line Usage

The `stor4build` command includes three subcommands at this time:

  * `run-icetank` - Runs the chiller-based ice tank Python plugin case with a specified capacity. Using `--chw` will use the chilled water version.
  * `size-icetank` - Runs the chiller-based ice tank Python plugin case with a size based on the baseline model and discharge window parameters. Using `--chw` will use the chilled water version.
  * `run-dxcoil` - Runs the native E+ DX coil TES system with autosizing.

Further information is available with the `--help` option.

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
stor4build --help
```

You should see the help output from the tool.

## Web API

A simple flask-based web api is included. To run it, a PostgreSQL database storing the baseline models and weather is required. That setup is not described here yet. The following four environment variables need to be set:

```
FLASK_TIMESCALE_HOST
FLASK_TIMESCALE_DB
FLASK_TIMESCALE_USERNAME
FLASK_TIMESCALE_PASSWORD
```

Standard password rules apply. To launch the back end (that does the calculation) run

```console
flask --app stor4build.api run
```

This will start up the flask **development** server and output will appear on the console. The API accepts JSON inputs in the form described in the `schema` directory in the file `stor4build.json`. Example inputs and scripts to send them to the API are in the `resources` and `scripts` directories.

## License

`stor4build` is distributed under the terms of the [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html) license.
