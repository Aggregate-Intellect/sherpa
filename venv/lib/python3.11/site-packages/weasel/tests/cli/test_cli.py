import os
import time

import pytest
import srsly

from weasel.cli.remote_storage import RemoteStorage
from weasel.schemas import ProjectConfigSchema, validate
from weasel.util import git_checkout, is_subpath_of, load_project_config, make_tempdir
from weasel.util import validate_project_commands


def test_issue11235():
    """
    Test that the cli handles interpolation in the directory names correctly when loading project config.
    """
    lang_var = "en"
    variables = {"lang": lang_var}
    commands = [{"name": "x", "script": ["hello ${vars.lang}"]}]
    directories = ["cfg", "${vars.lang}_model"]
    project = {"commands": commands, "vars": variables, "directories": directories}
    with make_tempdir() as d:
        srsly.write_yaml(d / "project.yml", project)
        cfg = load_project_config(d)
        # Check that the directories are interpolated and created correctly
        assert os.path.exists(d / "cfg")
        assert os.path.exists(d / f"{lang_var}_model")
    assert cfg["commands"][0]["script"][0] == f"hello {lang_var}"


def test_project_config_validation_full():
    config = {
        "vars": {"some_var": 20},
        "directories": ["assets", "configs", "corpus", "scripts", "training"],
        "assets": [
            {
                "dest": "x",
                "extra": True,
                "url": "https://example.com",
                "checksum": "63373dd656daa1fd3043ce166a59474c",
            },
            {
                "dest": "y",
                "git": {
                    "repo": "https://github.com/example/repo",
                    "branch": "develop",
                    "path": "y",
                },
            },
            {
                "dest": "z",
                "extra": False,
                "url": "https://example.com",
                "checksum": "63373dd656daa1fd3043ce166a59474c",
            },
        ],
        "commands": [
            {
                "name": "train",
                "help": "Train a model",
                "script": ["python -m spacy train config.cfg -o training"],
                "deps": ["config.cfg", "corpus/training.spcy"],
                "outputs": ["training/model-best"],
            },
            {"name": "test", "script": ["pytest", "custom.py"], "no_skip": True},
        ],
        "workflows": {"all": ["train", "test"], "train": ["train"]},
    }
    errors = validate(ProjectConfigSchema, config)
    assert not errors


@pytest.mark.parametrize(
    "config",
    [
        {"commands": [{"name": "a"}, {"name": "a"}]},
        {"commands": [{"name": "a"}], "workflows": {"a": []}},
        {"commands": [{"name": "a"}], "workflows": {"b": ["c"]}},
    ],
)
def test_project_config_validation1(config):
    with pytest.raises(SystemExit):
        validate_project_commands(config)


@pytest.mark.parametrize(
    "config,n_errors",
    [
        ({"commands": {"a": []}}, 1),
        ({"commands": [{"help": "..."}]}, 1),
        ({"commands": [{"name": "a", "extra": "b"}]}, 1),
        ({"commands": [{"extra": "b"}]}, 2),
        ({"commands": [{"name": "a", "deps": [123]}]}, 1),
    ],
)
def test_project_config_validation2(config, n_errors):
    errors = validate(ProjectConfigSchema, config)
    assert len(errors) == n_errors


@pytest.mark.parametrize(
    "parent,child,expected",
    [
        ("/tmp", "/tmp", True),
        ("/tmp", "/", False),
        ("/tmp", "/tmp/subdir", True),
        ("/tmp", "/tmpdir", False),
        ("/tmp", "/tmp/subdir/..", True),
        ("/tmp", "/tmp/..", False),
    ],
)
def test_is_subpath_of(parent, child, expected):
    assert is_subpath_of(parent, child) == expected


def test_local_remote_storage():
    with make_tempdir() as d:
        filename = "a.txt"

        content_hashes = ("aaaa", "cccc", "bbbb")
        for i, content_hash in enumerate(content_hashes):
            # make sure that each subsequent file has a later timestamp
            if i > 0:
                time.sleep(1)
            content = f"{content_hash} content"
            loc_file = d / "root" / filename
            if not loc_file.parent.exists():
                loc_file.parent.mkdir(parents=True)
            with loc_file.open(mode="w") as file_:
                file_.write(content)

            # push first version to remote storage
            remote = RemoteStorage(d / "root", str(d / "remote"))
            remote.push(filename, "aaaa", content_hash)

            # retrieve with full hashes
            loc_file.unlink()
            remote.pull(filename, command_hash="aaaa", content_hash=content_hash)
            with loc_file.open(mode="r") as file_:
                assert file_.read() == content

            # retrieve with command hash
            loc_file.unlink()
            remote.pull(filename, command_hash="aaaa")
            with loc_file.open(mode="r") as file_:
                assert file_.read() == content

            # retrieve with content hash
            loc_file.unlink()
            remote.pull(filename, content_hash=content_hash)
            with loc_file.open(mode="r") as file_:
                assert file_.read() == content

            # retrieve with no hashes
            loc_file.unlink()
            remote.pull(filename)
            with loc_file.open(mode="r") as file_:
                assert file_.read() == content


def test_local_remote_storage_pull_missing():
    # pulling from a non-existent remote pulls nothing gracefully
    with make_tempdir() as d:
        filename = "a.txt"
        remote = RemoteStorage(d / "root", str(d / "remote"))
        assert remote.pull(filename, command_hash="aaaa") is None
        assert remote.pull(filename) is None


def test_project_git_dir_asset():
    with make_tempdir() as d:
        # Use a very small repo.
        git_checkout(
            "https://github.com/explosion/os-signpost.git",
            "os_signpost",
            d / "signpost",
            branch="v0.0.3",
        )
        assert os.path.isdir(d / "signpost")


@pytest.mark.issue(66)
def test_project_git_file_asset():
    with make_tempdir() as d:
        # Use a very small repo.
        git_checkout(
            "https://github.com/explosion/os-signpost.git",
            "README.md",
            d / "readme.md",
            branch="v0.0.3",
        )
        assert os.path.isfile(d / "readme.md")
