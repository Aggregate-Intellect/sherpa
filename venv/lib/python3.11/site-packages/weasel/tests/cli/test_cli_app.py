from pathlib import Path
from typing import Any, Dict

import pytest
import srsly
from typer.testing import CliRunner

from weasel import app
from weasel.cli.main import HELP
from weasel.util import get_git_version

runner = CliRunner()


@pytest.mark.parametrize("cmd", [None, "--help"])
def test_show_help(cmd):
    """Basic test to confirm help text appears"""
    result = runner.invoke(app, [cmd] if cmd else None)
    for line in HELP.splitlines():
        assert line in result.stdout


def has_git():
    try:
        get_git_version()
        return True
    except RuntimeError:
        return False


SAMPLE_PROJECT: Dict[str, Any] = {
    "title": "Sample project",
    "description": "This is a project for testing",
    "assets": [
        {
            "dest": "assets/weasel-readme.md",
            "url": "https://github.com/explosion/weasel/raw/9a3632862b47069d2f9033b773e814d4c4e09c83/README.md",
            "checksum": "65f4c426a9b153b7683738c92d0d20f9",
        },
        {
            "dest": "assets/pyproject.toml",
            "url": "https://github.com/explosion/weasel/raw/9a3632862b47069d2f9033b773e814d4c4e09c83/pyproject.toml",
            "checksum": "1e2da3a3030d6611520952d5322cd94e",
            "extra": True,
        },
    ],
    "commands": [
        {
            "name": "ok",
            "help": "print ok",
            "script": ["python -c \"print('okokok')\""],
        },
        {
            "name": "create",
            "help": "make a file",
            "script": ["touch abc.txt"],
            "outputs": ["abc.txt"],
        },
        {
            "name": "clean",
            "help": "remove test file",
            "script": ["rm abc.txt"],
        },
    ],
}

SAMPLE_PROJECT_TEXT = srsly.yaml_dumps(SAMPLE_PROJECT)


@pytest.fixture
def project_dir(tmp_path: Path):
    path = tmp_path / "project"
    path.mkdir()
    (path / "project.yml").write_text(SAMPLE_PROJECT_TEXT)
    yield path


def test_project_document(project_dir: Path):
    readme_path = project_dir / "README.md"
    assert not readme_path.exists(), "README already exists"
    result = CliRunner().invoke(
        app, ["document", str(project_dir), "-o", str(readme_path)]
    )
    assert result.exit_code == 0
    assert readme_path.is_file()
    text = readme_path.read_text("utf-8")
    assert SAMPLE_PROJECT["description"] in text


def test_project_assets(project_dir: Path):
    asset_dir = project_dir / "assets"
    assert not asset_dir.exists(), "Assets dir is already present"
    result = CliRunner().invoke(app, ["assets", str(project_dir)])
    assert result.exit_code == 0
    assert (asset_dir / "weasel-readme.md").is_file(), "Assets not downloaded"
    # check that extras work
    result = CliRunner().invoke(app, ["assets", "--extra", str(project_dir)])
    assert result.exit_code == 0
    assert (asset_dir / "pyproject.toml").is_file(), "Extras not downloaded"


def test_project_run(project_dir: Path):
    # make sure dry run works
    test_file = project_dir / "abc.txt"
    result = CliRunner().invoke(app, ["run", "--dry", "create", str(project_dir)])
    assert result.exit_code == 0
    assert not test_file.is_file()
    result = CliRunner().invoke(app, ["run", "create", str(project_dir)])
    assert result.exit_code == 0
    assert test_file.is_file()
    result = CliRunner().invoke(app, ["run", "ok", str(project_dir)])
    assert result.exit_code == 0
    assert "okokok" in result.stdout


def test_check_spacy_env_vars(project_dir: Path, monkeypatch: pytest.MonkeyPatch):
    # make sure dry run works
    project_dir / "abc.txt"

    result = CliRunner().invoke(app, ["run", "--dry", "create", str(project_dir)])
    assert result.exit_code == 0
    assert (
        "You've set a `SPACY_CONFIG_OVERRIDES` environment variable"
        not in result.output
    )
    assert (
        "You've set a `SPACY_PROJECT_USE_GIT_VERSION` environment variable"
        not in result.output
    )

    monkeypatch.setenv("SPACY_CONFIG_OVERRIDES", "test")
    monkeypatch.setenv("SPACY_PROJECT_USE_GIT_VERSION", "false")

    result = CliRunner().invoke(app, ["run", "--dry", "create", str(project_dir)])
    assert result.exit_code == 0

    assert "You've set a `SPACY_CONFIG_OVERRIDES` environment variable" in result.output
    assert (
        "You've set a `SPACY_PROJECT_USE_GIT_VERSION` environment variable"
        in result.output
    )


@pytest.mark.skipif(not has_git(), reason="git not installed")
@pytest.mark.parametrize(
    "options_string",
    [
        "",
        # "--sparse",
        "--branch v3",
        "--repo https://github.com/explosion/projects --branch v3",
    ],
)
def test_project_clone(tmp_path: Path, options_string: str):
    out = tmp_path / "project_clone"
    target = "benchmarks/ner_conll03"
    if not options_string:
        options = []
    else:
        options = options_string.split()
    result = CliRunner().invoke(app, ["clone", target, *options, str(out)])
    assert result.exit_code == 0
    assert "weasel assets" in result.output
    assert (out / "README.md").is_file()


def test_project_push_pull(tmp_path: Path, project_dir: Path):
    proj = dict(SAMPLE_PROJECT)
    remote = "xyz"

    remote_dir = tmp_path / "remote"
    remote_dir.mkdir()

    proj["remotes"] = {remote: str(remote_dir)}
    proj_text = srsly.yaml_dumps(proj)
    (project_dir / "project.yml").write_text(proj_text)

    test_file = project_dir / "abc.txt"
    result = CliRunner().invoke(app, ["run", "create", str(project_dir)])
    assert result.exit_code == 0
    assert test_file.is_file()
    result = CliRunner().invoke(app, ["push", remote, str(project_dir)])
    assert result.exit_code == 0
    result = CliRunner().invoke(app, ["run", "clean", str(project_dir)])
    assert result.exit_code == 0
    assert not test_file.exists()
    result = CliRunner().invoke(app, ["pull", remote, str(project_dir)])
    assert result.exit_code == 0
    assert test_file.is_file()
