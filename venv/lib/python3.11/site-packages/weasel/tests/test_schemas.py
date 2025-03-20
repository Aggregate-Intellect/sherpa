from pathlib import Path

import pytest
import srsly
from typer.testing import CliRunner

from weasel import app

EXAMPLES = [
    (dict(title="Test"), False),
    (dict(title="Test", spacy_version=""), True),
    (dict(title="Test", spacy_version="3.4.1"), True),
]


@pytest.fixture
def project_dir(tmp_path: Path):
    path = tmp_path / "project"
    path.mkdir()
    yield path


@pytest.mark.parametrize("conf,should_warn", EXAMPLES)
def test_project_document(project_dir: Path, conf, should_warn):
    config = srsly.yaml_dumps(conf)

    (project_dir / "project.yml").write_text(config)

    result = CliRunner().invoke(app, ["document", str(project_dir)])
    assert result.exit_code == 0
    assert (
        "Your project configuration file includes a `spacy_version` key, "
        in result.output
    ) is should_warn
