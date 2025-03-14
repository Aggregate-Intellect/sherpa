import pytest

from .util import load_logger_from_config


valid_config_string = """
[nlp]
lang = "en"
pipeline = ["tok2vec"]

[components]

[components.tok2vec]
factory = "tok2vec"

[training]

[training.logger]
@loggers = "spacy.ChainLogger.v1"
logger1 = {"@loggers": "spacy.ConsoleLogger.v1", "progress_bar": "true"}
logger9 = {"@loggers": "spacy.LookupLogger.v1", "patterns": ["test"]}
"""

invalid_config_string = """
[nlp]
lang = "en"
pipeline = ["tok2vec"]

[components]

[components.tok2vec]
factory = "tok2vec"

[training]

[training.logger]
@loggers = "spacy.ChainLogger.v1"
"""


def test_load_from_config():
    valid_logger, nlp = load_logger_from_config(valid_config_string)
    valid_logger(nlp)

    with pytest.raises(ValueError, match="No loggers"):
        invalid_logger, nlp = load_logger_from_config(invalid_config_string)
        invalid_logger(nlp)
