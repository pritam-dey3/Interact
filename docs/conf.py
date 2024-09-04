# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))

project = "Interact"
copyright = "2023, Pritam Dey"
author = "Pritam Dey"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autobuild",
    "sphinx.ext.githubpages",
    "sphinxcontrib.mermaid",
]
autodoc_typehints = "description"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "examples"]

language = "en"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_sidebars = {
    '**': [
        'getting-started.html',
        'base.html',
        'handlers.html',
        'similarity.html',
        'examples.html',
    ]
}


def setup(app):
    project_root = Path(__file__).parent.parent
    example_files = list((project_root / "examples").glob("*.py"))
    docs_example_dir = project_root / "docs" / "examples_docs"
    docs_example_dir.mkdir(exist_ok=True, parents=True)

    example_file_patter = """\
{heading}

.. literalinclude:: {path}
    """

    for file in example_files:
        heading = file.stem + "\n" + "=" * len(file.stem)
        path = "../../" + file.relative_to(project_root).as_posix()
        with open(docs_example_dir / f"{file.stem}.rst", "w+") as f:
            f.write(example_file_patter.format(heading=heading, path=path))

    index_file_pattern = """\
Examples
========

.. toctree::
    :maxdepth: 1
    :glob:

    examples_docs/*
    """

    with open(project_root / "docs" / "examples_toc.rst", "w+") as f:
        f.write(index_file_pattern)