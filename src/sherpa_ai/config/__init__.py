"""
App configuration settings.

Usage:

    First define variables in runtime environment or in your `.env` file.
    See `.env-sample` file for examples and a useful starting point.
    Then, in your code, use the values like this:

        import Config as cfg
        secret = cfg.SLACK_SIGNING_SECRET
        another_variable = cfg.ANOTHER_ENVIRONMENT_VARIABLE

To add, remove, or change variables, ...
1. Update this file to create the variables
2. Update `env-sample` to match
3. Update your own `.env` file and test the changes
4. Update corresponding secrets in Github and deployment environments
"""

import subprocess
import sys
from os import environ, path

from dotenv import find_dotenv, load_dotenv
from loguru import logger

from sherpa_ai.config.task_config import AgentConfig


env_path = find_dotenv(usecwd=True)
load_dotenv(env_path)


# A list of configuration values deemed to be sensitive, e.g. API keys, secrets.
# These values should not be shared with external tools such as exception reporting services.
# Make sure to add new variables to this list as appropriate so that it stays up to date.
SENSITIVE_SETTINGS_AND_SECRETS = [
    "OPENAI_API_KEY",
    "SLACK_SIGNING_SECRET",
    "SLACK_OAUTH_TOKEN",
    "SLACK_VERIFICATION_TOKEN",
    "PINECONE_API_KEY",
    "SERPER_API_KEY",
    "GITHUB_AUTH_TOKEN",
    "AWS_ACCESS_KEY",
    "AWS_SECRET_KEY",
    "ROLLBAR_ACCESS_TOKEN",
]


# Logging configuration. For local development, typically use DEBUG or INFO.
LOG_LEVEL = environ.get("LOG_LEVEL", "INFO").upper()

# Sherpa's deployment environment name. development, production, github_actions, etc.
SHERPA_ENV = environ.get("SHERPA_ENV")

# Flask debug mode. Optional. Useful for local development.
# Never enable debug mode in production, as doing so creates security risks.
FLASK_DEBUG = environ.get("FLASK_DEBUG", False) == "True"

# Language model settings
OPENAI_API_KEY = environ.get("OPENAI_API_KEY")
TEMPERATURE = environ.get("TEMPERATURE") or 0
DAILY_TOKEN_LIMIT = float(environ.get("DAILY_TOKEN_LIMIT") or 20000)
DAILY_LIMIT_REACHED_MESSAGE = (
    environ.get("DAILY_LIMIT_REACHED_MESSAGE")
    or "Sorry for the inconvenience, but it seems that you have exceeded your daily token limit. As a result, you will need to try again after 24 hours. Thank you for your understanding."
)
LIMIT_TIME_SIZE_IN_HOURS = environ.get("LIMIT_TIME_SIZE_IN_HOURS") or "24"
FILE_SIZE_LIMIT = environ.get("FILE_SIZE_LIMIT") or 2097152
FILE_TOKEN_LIMIT = environ.get("FILE_TOKEN_LIMIT") or 20000
DB_NAME = environ.get("DB_NAME") or "sqlite:///token_counter.db"

# Slack integration
SLACK_SIGNING_SECRET = environ.get("SLACK_SIGNING_SECRET")
SLACK_OAUTH_TOKEN = environ.get("SLACK_OAUTH_TOKEN")
SLACK_VERIFICATION_TOKEN = environ.get("SLACK_VERIFICATION_TOKEN")
SLACK_PORT = environ.get("SLACK_PORT", 3000)

# Vector database settings, for embeddings. Choose from Pinecone or Chroma.
# If none is configured, Sherpa uses an in-memory version of Chroma. If you're running
# Sherpa via docker-compose, Docker settings are used instead of these values.

# Pinecone. Optional. Enables cloud-based storage of vector embeddings.
PINECONE_API_KEY = environ.get("PINECONE_API_KEY")
PINECONE_NAMESPACE = environ.get("PINECONE_NAMESPACE", "ReadTheDocs")
PINECONE_ENV = environ.get("PINECONE_ENV")
PINECONE_INDEX = environ.get("PINECONE_INDEX")
INDEX_NAME_FILE_STORAGE = environ.get("INDEX_NAME_FILE_STORAGE", "sherpa_db")

# Chroma. Optional. Enables local, docker or cloud based storage of vector embeddings.
CHROMA_HOST = environ.get("CHROMA_HOST")
CHROMA_PORT = environ.get("CHROMA_PORT")
CHROMA_INDEX = environ.get("CHROMA_INDEX")

# Serper.dev. Optional. Enables Google web search capability in Sherpa.
SERPER_API_KEY = environ.get("SERPER_API_KEY")

# Github auth for extracting readme files from GitHub repositories. Optional.
GITHUB_AUTH_TOKEN = environ.get("GITHUB_AUTH_TOKEN")

# Amazon Web Sevices - for transcript summaries. Optional.
AWS_ACCESS_KEY = environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = environ.get("AWS_SECRET_KEY")

# Settings for exception tracking with Rollbar https://rollbar.com/. Optional.
ROLLBAR_ACCESS_TOKEN = environ.get("ROLLBAR_ACCESS_TOKEN")


# Configure logger. To get JSON serialization, set serialize=True.
# See https://loguru.readthedocs.io/en/stable/ for info on Loguru features.
logger.remove(0)  # remove the default handler configuration
logger.add(sys.stderr, level=LOG_LEVEL, serialize=False)


# `this` is a pointer to the module object instance itself.
this = sys.modules[__name__]


def check_settings_and_warn():
    """Warns user if important environment variables are not set"""
    if (
        this.PINECONE_API_KEY
        and this.PINECONE_NAMESPACE
        and this.PINECONE_ENV
        and this.PINECONE_INDEX
    ):
        logger.info(
            "Config: Pinecone environment variables are set. Using Pinecone database."
        )
        this.VECTORDB = "pinecone"
    elif this.CHROMA_HOST and this.CHROMA_PORT and this.CHROMA_INDEX:
        logger.info(
            "Config: Chroma environment variables are set. Using Chroma database."
        )
        this.VECTORDB = "chroma"
    else:
        logger.warning(
            "Config: No vector database environment variables are set. "
            "Using in-memory Chroma database. This may not be what you intended."
        )
        this.VECTORDB = "in-memory"

    if None in [
        this.SLACK_VERIFICATION_TOKEN,
        this.SLACK_SIGNING_SECRET,
        this.SLACK_OAUTH_TOKEN,
        this.SLACK_PORT,
    ]:
        logger.warning("Config: Slack environment variables not set")
    else:
        logger.info("Config: Slack environment variables are set")

    if this.OPENAI_API_KEY is None:
        logger.warning("Config: OpenAI environment variables not set")
    else:
        logger.info("Config: OpenAI environment variables are set")


check_settings_and_warn()


def current_app_revision_from_file_or_git():
    """Returns current git revision hash, either from a file (preferred) or by calling git"""

    git_commit_hash = None

    # A build process is expected to create this file, e.g. in production
    if path.exists("./git-sha1.txt"):
        with open("./git-sha1.txt", "r") as f:
            git_commit_hash = f.read().strip()

    # Alternaively we expect git to be installed, so we use git directly
    else:
        git_commit_hash = current_git_revision_short_hash()
    return git_commit_hash


def current_git_revision_short_hash():
    """Returns short form of the current git revision hash, or None if it's unavailable"""

    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("ascii")
            .strip()
        )
    except Exception:
        return None


__all__ = [
    "AgentConfig",
    "current_app_revision_from_file_or_git",
]
