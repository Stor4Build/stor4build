# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

about: dict[str, str] = {}
exec((SRC / "stor4build" / "__about__.py").read_text(encoding="utf-8"), about)

project = "stor4build"
author = "Oak Ridge National Laboratory and contributors"
copyright = "2024-present, Oak Ridge National Laboratory and contributors"
release = about["__version__"]
version = release

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "sphinxcontrib.openapi",
]

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
myst_heading_anchors = 3

autodoc_member_order = "bysource"
autodoc_typehints = "description"

html_theme = "furo"
html_title = "stor4build documentation"

latex_documents = [
    (master_doc, "stor4build.tex", "stor4build Documentation", author, "manual"),
]
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
}