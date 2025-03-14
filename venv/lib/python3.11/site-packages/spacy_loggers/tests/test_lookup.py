import pytest
import re

from spacy_loggers.util import matcher_for_regex_patterns
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
@loggers = "spacy.LookupLogger.v1"
patterns = ["^[pP]ytorch", "zeppelin" ]
"""

invalid_config_string_empty = """
[nlp]
lang = "en"
pipeline = ["tok2vec"]

[components]

[components.tok2vec]
factory = "tok2vec"

[training]

[training.logger]
@loggers = "spacy.LookupLogger.v1"
patterns = []
"""

invalid_config_string_incorrect_pattern = """
[nlp]
lang = "en"
pipeline = ["tok2vec"]

[components]

[components.tok2vec]
factory = "tok2vec"

[training]

[training.logger]
@loggers = "spacy.LookupLogger.v1"
patterns = [")"]
"""


def test_load_from_config():
    valid_logger, nlp = load_logger_from_config(valid_config_string)
    valid_logger(nlp)

    with pytest.raises(ValueError, match="at least one pattern"):
        invalid_logger, nlp = load_logger_from_config(invalid_config_string_empty)
        invalid_logger(nlp)

    with pytest.raises(ValueError, match="couldn't be compiled"):
        invalid_logger, nlp = load_logger_from_config(
            invalid_config_string_incorrect_pattern
        )
        invalid_logger(nlp)


def test_custom_stats_matcher():
    patterns = ["^[pP]ytorch", "zeppelin$"]
    inputs = [
        "no match",
        "torch",
        "pYtorch",
        "pytorch",
        "Pytorch 1.13",
        "led zeppelin",
    ]
    outputs = [False, False, False, True, True, True]

    matcher = matcher_for_regex_patterns(patterns)
    assert [matcher(x) for x in inputs] == outputs

    with pytest.raises(ValueError, match="couldn't be compiled"):
        matcher_for_regex_patterns([")"])
