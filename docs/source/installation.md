# Installation

The `stor4build` can be installed from PyPI:

```console
pip install stor4build
```

The command line entry point is `stor4build`:

```console
stor4build --help
```

## External Tools, Packages, and Python

`stor4build` simulation workflows depend on OpenStudio and EnergyPlus, so the appropriate version of OpenStudio will need to be installed:

> As of stor4build version 1.0.0, OpensStudio version 3.11 is required, which supports EnergyPlus 25.2 and Python 3.12

The CLI assumes that the OpenStudio executable is available as `openstudio` unless a command provides an `--openstudio` option. The tool uses an EnergyPlus plugin that requires Python packages in the version of Python supported by EnergyPlus:

  - scipy
  - SecondaryCoolantProps

If the system Python version matches the version supported by EnergyPlus, installing the `stor4build` package via `pip` will install the dependencies and no further work is needed. If the system Python version is different, then the packages will need to be provided for Python 3.12 via another path (for example, a correctly versioned virtual environment). The "site packages" directory may be passed to the plugin via the `--custom-site-packages` command line argument.

## Development Environment

Development of the tool will be easiest using a project management tool to handle the versioning issue. Main development is current done using the Hatch tool, but other tools provide similar functionality. Install Hatch and create the default environment:

```console
pip install hatch
hatch env create
```

Run the test suite with:

```console
hatch run pytest
```

Build this documentation locally with:

```console
hatch run docs:html
```

Generate the LaTeX sources without compiling a PDF with:

```console
hatch run docs:latex
```

Build the PDF manual with:

```console
hatch run docs:pdf
```

The PDF build requires a working LaTeX installation with `latexmk` available on `PATH` in addition to the Python documentation dependencies. On Windows, `latexmk` will also need a working `perl`, which is not typically available on Windows machines.