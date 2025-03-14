import pytest
from spacy import registry

FUNCTIONS = [
    ("loggers", "spacy.WandbLogger.v1"),
    ("loggers", "spacy.WandbLogger.v2"),
    ("loggers", "spacy.WandbLogger.v3"),
    ("loggers", "spacy.WandbLogger.v4"),
    ("loggers", "spacy.WandbLogger.v5"),
    ("loggers", "spacy.MLflowLogger.v1"),
    ("loggers", "spacy.MLflowLogger.v2"),
    ("loggers", "spacy.ClearMLLogger.v1"),
    ("loggers", "spacy.ClearMLLogger.v2"),
    ("loggers", "spacy.ChainLogger.v1"),
    ("loggers", "spacy.PyTorchLogger.v1"),
    ("loggers", "spacy.LookupLogger.v1"),
    ("loggers", "spacy.CupyLogger.v1"),
]


@pytest.mark.parametrize("reg_name,func_name", FUNCTIONS)
def test_registry(reg_name, func_name):
    assert registry.has(reg_name, func_name)
    assert registry.get(reg_name, func_name)
