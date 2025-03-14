import pytest
import srsly
from confection import ConfigValidationError

from weasel.schemas import ProjectConfigSchema, validate
from weasel.util import is_subpath_of, load_project_config, make_tempdir
from weasel.util import substitute_project_variables, validate_project_commands


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
    "int_value",
    [10, pytest.param("10", marks=pytest.mark.xfail)],
)
def test_project_config_interpolation(int_value):
    variables = {"a": int_value, "b": {"c": "foo", "d": True}}
    commands = [
        {"name": "x", "script": ["hello ${vars.a} ${vars.b.c}"]},
        {"name": "y", "script": ["${vars.b.c} ${vars.b.d}"]},
    ]
    project = {"commands": commands, "vars": variables}
    with make_tempdir() as d:
        srsly.write_yaml(d / "project.yml", project)
        cfg = load_project_config(d)
    assert type(cfg) == dict
    assert type(cfg["commands"]) == list
    assert cfg["commands"][0]["script"][0] == "hello 10 foo"
    assert cfg["commands"][1]["script"][0] == "foo true"
    commands = [{"name": "x", "script": ["hello ${vars.a} ${vars.b.e}"]}]
    project = {"commands": commands, "vars": variables}
    with pytest.raises(ConfigValidationError):
        substitute_project_variables(project)


@pytest.mark.parametrize(
    "greeting",
    [342, "everyone", "tout le monde", pytest.param("42", marks=pytest.mark.xfail)],
)
def test_project_config_interpolation_override(greeting):
    variables = {"a": "world"}
    commands = [
        {"name": "x", "script": ["hello ${vars.a}"]},
    ]
    overrides = {"vars.a": greeting}
    project = {"commands": commands, "vars": variables}
    with make_tempdir() as d:
        srsly.write_yaml(d / "project.yml", project)
        cfg = load_project_config(d, overrides=overrides)
    assert type(cfg) == dict
    assert type(cfg["commands"]) == list
    assert cfg["commands"][0]["script"][0] == f"hello {greeting}"


def test_project_config_interpolation_env(monkeypatch: pytest.MonkeyPatch):
    variables = {"a": 10}
    env_var = "SPACY_TEST_FOO"

    env_vars = {"foo": env_var}
    commands = [{"name": "x", "script": ["hello ${vars.a} ${env.foo}"]}]
    project = {"commands": commands, "vars": variables, "env": env_vars}

    with make_tempdir() as d:
        srsly.write_yaml(d / "project.yml", project)
        cfg = load_project_config(d)
    assert cfg["commands"][0]["script"][0] == "hello 10 "

    monkeypatch.setenv(env_var, "123")

    with make_tempdir() as d:
        srsly.write_yaml(d / "project.yml", project)
        cfg = load_project_config(d)
    assert cfg["commands"][0]["script"][0] == "hello 10 123"
