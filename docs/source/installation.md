# Installation

Stor4Build can be installed from PyPI:

```console
pip install stor4build
```

The command line entry point is `stor4build`:

```console
stor4build --help
```

## External Tools

Stor4Build simulation workflows depend on OpenStudio and EnergyPlus. The CLI assumes that the OpenStudio executable is available as `openstudio` unless a command provides an `--openstudio` option.

## Development Environment

For repository development, install Hatch and create the default environment:

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

The PDF build requires a working LaTeX installation with `latexmk` available on `PATH` in addition to the Python documentation dependencies.