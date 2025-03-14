from pathlib import Path

import pytest
from typer.testing import CliRunner

from weasel import app

from .test_cli_app import has_git

runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path_factory: pytest.TempPathFactory):
    # a working directory for the session
    base = tmp_path_factory.mktemp("project")
    return base / "project"


@pytest.fixture
def remote_url(tmp_path_factory: pytest.TempPathFactory):
    # a "remote" for testing
    base = tmp_path_factory.mktemp("remote")
    return base / "remote"


@pytest.fixture
def clone(project_dir: Path):
    """Cloning shouldn't fail"""
    repo = "https://github.com/explosion/weasel"
    branch = "main"
    result = runner.invoke(
        app,
        [
            "clone",
            "--repo",
            repo,
            "--branch",
            branch,
            "weasel/tests/demo_project",
            str(project_dir),
        ],
    )

    assert result.exit_code == 0
    assert (project_dir / "project.yml").exists()


@pytest.fixture(autouse=True)
def assets(clone, project_dir: Path):
    result = runner.invoke(app, ["assets", str(project_dir)])

    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "assets/README.md").exists()


@pytest.mark.skipif(not has_git(), reason="git not installed")
def test_remote(project_dir: Path, remote_url: Path):
    result = runner.invoke(app, ["assets", str(project_dir)])
    assert result.exit_code == 0
    assert (project_dir / "assets/README.md").exists()

    result = runner.invoke(app, ["run", "prep", str(project_dir)])
    assert result.exit_code == 0

    # append remote to the file
    with open(project_dir / "project.yml", "a") as project_file:
        project_file.write(f"\nremotes:\n    default: {remote_url}\n")

    result = runner.invoke(app, ["push", "default", str(project_dir)])
    assert result.exit_code == 0

    # delete a file, and make sure pull restores it
    (project_dir / "corpus/stuff.txt").unlink()

    result = runner.invoke(app, ["pull", "default", str(project_dir)])
    assert result.exit_code == 0
    assert (project_dir / "corpus/stuff.txt").exists()
