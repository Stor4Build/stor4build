# Documentation Development

The documentation source lives in `docs/source`. Generated files are written under `docs/_build` and are ignored by git.

Build the HTML documentation:

```console
hatch run docs:html
```

Generate the LaTeX sources without compiling a PDF:

```console
hatch run docs:latex
```

Build the PDF documentation:

```console
hatch run docs:pdf
```

Check external links:

```console
hatch run docs:linkcheck
```

The web version is intended to be deployed to GitHub Pages from the generated Sphinx HTML. The PDF version is produced from the same source with Sphinx's LaTeX builder and requires `latexmk` on `PATH`.

## Authoring Notes

Use Markdown for narrative documentation. Keep more durable content in user-facing guides and examples, and keep more volatile command/API details generated from the implementation (i.e., the docstrings) whenever possible.

When the FastAPI implementation becomes the active web API, generate an OpenAPI document from the app and render it into the reference section rather than hand-maintaining endpoint details.