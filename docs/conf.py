# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'Sherpa - Thinking Companion'
copyright = '2023, Aggregate Intellect Inc.'
author = 'Amir Feizpour et al'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx_design"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_permalinks_icon = '<span>#</span>'
html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": "https://github.com/Aggregate-Intellect/sherpa",
    "use_repository_button": True,
    "use_download_button": False,
    "use_issues_button": True,
    "home_page_in_toc": True,
    "show_navbar_depth": 1,
    "show_toc_level": 3,
    "toc_title": "In This Page:",
}
html_title = "Sherpa - Thinking Companion"
html_logo = "Open Book/cover_image.png"
html_favicon = ""


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']