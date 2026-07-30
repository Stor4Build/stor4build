# Stor4Build Modeling Tool

[![PyPI - Version](https://img.shields.io/pypi/v/stor4build.svg)](https://pypi.org/project/stor4build)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stor4build.svg)](https://pypi.org/project/stor4build)

-----

**Table of Contents**

- [Installation](#installation)
- [Command Line Usage](#command-line-usage)
- [VS Code/Hatch Dev Environment](#vs-codehatch-dev-environment)
- [Web API](#web-api)
- [Prototype Coverage](#prototype-coverage)
- [License](#license)

## Installation

```console
pip install stor4build
```

## Command Line Usage

The `stor4build` command includes three subcommands at this time:

  * `run-icetank` - Runs the chiller-based ice tank Python plugin case with a specified capacity. Using `--chw` will use the chilled water version.
  * `size-icetank` - Runs the chiller-based ice tank Python plugin case with a size based on the baseline model and discharge window parameters. Using `--chw` will use the chilled water version.
  * `run-icetank-dynamic` - Runs an iterative simulation process that optimizes the charging schedule based on electricity rates and demand charges.
  * `run-dxcoil` - Runs the native E+ DX coil packaged ice TES system with autosizing.

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

## Prototype Coverage

The tool now supports the majority of the OpenStudio prototypes. Three models (Laboratory, LargeDataCenterLowITE, and LargeDataCenterHighITE) are only available for vintages 2004 and later, so these models are not available before 2004. 

|          Type          |     Supported TES    | pre1980 | post1980 | 2004 | 2007 | 2010 | 2013 | 2016 | 2019 |
|:----------------------:|:--------------------:|:-------:|:--------:|:----:|:----:|:----:|:----:|:----:|:----:|
|       LargeOffice      |     ThermalTank      |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|       SmallOffice      | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|    RetailStandalone    | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|      MediumOffice      | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|       Courthouse       |     ThermalTank      |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|       Warehouse        | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|        College         |     ThermalTank      |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
| QuickServiceRestaurant | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|    RetailStripmall     | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
| FullServiceRestaurant  | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|       Laboratory       | DX coil packaged ice |     -   |     -    |   X  |   X  |   X  |   X  |   X  |   X  |
|      PrimarySchool     | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|       LargeHotel       |     ThermalTank      |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|        Hospital        |     ThermalTank      |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|       SmallHotel       |          TBD         |     -   |     -    |   -  |   -  |   -  |   -  |   -  |   -  |
|     SecondarySchool    | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
|       Outpatient       | DX coil packaged ice |     X   |     X    |   X  |   X  |   X  |   X  |   X  |   X  |
| LargeDataCenterLowITE  |     ThermalTank      |     -   |     -    |   X  |   X  |   X  |   X  |   X  |   X  |
| LargeDataCenterHighITE |     ThermalTank      |     -   |     -    |   X  |   X  |   X  |   X  |   X  |   X  |
|    MidriseApartment    |          TBD         |     -   |     -    |   -  |   -  |   -  |   -  |   -  |   -  |
|    HighriseApartment   |          TBD         |     -   |     -    |   -  |   -  |   -  |   -  |   -  |   -  |
| SmallDataCenterHighITE |          TBD         |     -   |     -    |   -  |   -  |   -  |   -  |   -  |   -  |
|  SmallDataCenterLowITE |          TBD         |     -   |     -    |   -  |   -  |   -  |   -  |   -  |   -  |

## License

`stor4build` is distributed under the terms of the [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html) license.
