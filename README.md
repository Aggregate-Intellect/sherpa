# 🤖 SHERPA - THINKING COMPANION

<img src="https://sherpa-ai.readthedocs.io/en/latest/_static/cover_image.png" width="200" height="200" />

![PyPI - Version](https://img.shields.io/pypi/v/sherpa-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

To see the documentation, visit: https://sherpa-ai.readthedocs.io/

## Quick Install

### From source (with [poetry](https://python-poetry.org/)):
```bash
git clone https://github.com/Aggregate-Intellect/sherpa
cd sherpa/src
poetry install
```

Some dependencies such as `chromadb` or `sentence-transformers` are optional and only required to run some specific functionalities (such as the DocumentSearch action). These dependencies are not install by default. You can either install them separated as needed, all install the entire suite using the `--with` flag from `poetry`:
```bash
poetry install --with optional
```
Similarly, you can install dependencies for testing and linting:
```bash
poetry install --with optional,test,lint
```

### From source (with pip editable mode):
```bash
git clone
cd sherpa/src
pip install -e .
```

### spaCy language model (entity validation only)

The `spacy` library is a core dependency and is always installed. Its `en_core_web_sm` language model is not, because it is distributed as a direct-URL wheel and PyPI rejects those in published package metadata.

Install it only if you enable entity validation — `EntityValidation` or `EntityValidationAction`, which are off by default (`BaseAgent.validations` is empty):
```bash
python -m spacy download en_core_web_sm
```
From a source checkout, `make install` already does this for you.

Without the model, entity validation raises an error telling you to run the command above. Nothing else in Sherpa uses it.

## Usage
Please refer to the documentation for the list of tutorials on using Sherpa: https://sherpa-ai.readthedocs.io/en/latest/How_To/tutorials.html

## Contributions Guideline

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it’s:

- Reporting a bug
- Discussing the current state of the book or the accompanying software
- Submitting a fix
- Proposing new features
- Becoming a maintainer

To get started, visit: https://sherpa-ai.readthedocs.io/en/latest/How_To/contribute.html
