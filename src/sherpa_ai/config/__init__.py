"""
App configuration settings.

Usage:

    First define variables in runtime environment or in your `.env` file.
    Then, ...

    import Config as cfg
    secret = cfg.SLACK_SIGNING_SECRET
    another_variable = cfg.ANOTHER_ENVIRONMENT_VARIABLE
"""

import sys
from os import environ

from dotenv import find_dotenv, load_dotenv
from loguru import logger

from sherpa_ai.config.task_config import AgentConfig

env_path = find_dotenv(usecwd=True)
load_dotenv(env_path)


AWS_ACCESS_KEY = environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = environ.get("AWS_SECRET_KEY")
FLASK_DEBUG = environ.get("FLASK_DEBUG", False) == "True"
GITHUB_AUTH_TOKEN = environ.get("GITHUB_AUTH_TOKEN")
SLACK_SIGNING_SECRET = environ.get("SLACK_SIGNING_SECRET")
SLACK_OAUTH_TOKEN = environ.get("SLACK_OAUTH_TOKEN")
SLACK_VERIFICATION_TOKEN = environ.get("SLACK_VERIFICATION_TOKEN")
SLACK_PORT = environ.get("SLACK_PORT", 3000)
OPENAI_API_KEY = environ.get("OPENAI_API_KEY")
TEMPRATURE = environ.get("TEMPRATURE") or 0

# Pinecone settings
PINECONE_API_KEY = environ.get("PINECONE_API_KEY")
PINECONE_NAMESPACE = environ.get("PINECONE_NAMESPACE", "ReadTheDocs")
PINECONE_ENV = environ.get("PINECONE_ENV")
PINECONE_INDEX = environ.get("PINECONE_INDEX")

# Chroma settings
CHROMA_HOST = environ.get("CHROMA_HOST")
CHROMA_PORT = environ.get("CHROMA_PORT")
CHROMA_INDEX = environ.get("CHROMA_INDEX")

SERPER_API_KEY = environ.get("SERPER_API_KEY")
LOG_LEVEL = environ.get("LOG_LEVEL", "INFO").upper()

# Usage setting
DAILY_TOKEN_LIMIT =  float(environ.get("DAILY_TOKEN_LIMIT") or 20000)
DAILY_LIMIT_REACHED_MESSAGE = (
    environ.get("DAILY_LIMIT_REACHED_MESSAGE")
    or "Sorry for the inconvenience, but it seems that you have exceeded your daily token limit. As a result, you will need to try again after 24 hours. Thank you for your understanding."
)
LIMIT_TIME_SIZE_IN_HOURS = environ.get("LIMIT_TIME_SIZE_IN_HOURS") or "24"
FILE_SIZE_LIMIT = environ.get("FILE_SIZE_LIMIT") or 2097152
FILE_TOKEN_LIMIT = environ.get("FILE_TOKEN_LIMIT") or 20000
DB_NAME = environ.get("DB_NAME") or "sqlite:///token_counter.db"

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
    logger.info("Config: Slack environment variables not set, unable to run")
    raise SystemExit(1)
else:
    logger.info("Config: Slack environment variables are set")

if this.OPENAI_API_KEY is None:
    logger.info("Config: OpenAI environment variables not set, unable to run")
    raise SystemExit(1)
else:
    logger.info("Config: OpenAI environment variables are set")

check_vectordb_setting()

__all__ = [
    "AgentConfig",
]
