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

import sys
from os import environ

from dotenv import find_dotenv, load_dotenv
from loguru import logger

from sherpa_ai.config.task_config import AgentConfig


env_path = find_dotenv(usecwd=True)
load_dotenv(env_path)


# Logging configuration. For local development, typically use DEBUG or INFO.
LOG_LEVEL = environ.get("LOG_LEVEL", "INFO").upper()

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
DB_NAME = environ.get("DB_NAME") or "token_counter.db"
DB_URL = environ.get("DB_URL") or "sqlite:///token_counter.db"

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

# Configure logger. To get JSON serialization, set serialize=True.
# See https://loguru.readthedocs.io/en/stable/ for info on Loguru features.
logger.remove(0)  # remove the default handler configuration
logger.add(sys.stderr, level=LOG_LEVEL, serialize=False)


# `this` is a pointer to the module object instance itself.
this = sys.modules[__name__]


def check_vectordb_setting():
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


# Ensure all mandatory environment variables are set, otherwise exit
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

check_vectordb_setting()

__all__ = [
    "AgentConfig",
]
