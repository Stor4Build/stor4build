# Stor4Build Documentation

The Sphinx documentation source lives in `docs/source`.

Build the HTML documentation with:

```console
hatch run docs:html
```

Generate the LaTeX sources with:

```console
hatch run docs:latex
```

Build the PDF manual with:

```console
hatch run docs:pdf
```

The PDF build requires a LaTeX distribution with `latexmk` available on `PATH`. Generated documentation output is written to `docs/_build` and is ignored by git.
