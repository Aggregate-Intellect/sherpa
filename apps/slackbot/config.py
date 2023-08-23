"""
App configuration settings.

Usage:

    First define variables in runtime environment or in your `.env` file.
    Then, ...

    import Config as cfg
    secret = cfg.SLACK_SIGNING_SECRET
    another_variable = cfg.ANOTHER_ENVIRONMENT_VARIABLE
"""

from loguru import logger
import sys
from os import environ

from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = environ.get("AWS_SECRET_KEY")
FLASK_DEBUG = environ.get("FLASK_DEBUG", False) == "True"
GITHUB_AUTH_TOKEN = environ.get("GITHUB_AUTH_TOKEN")
SLACK_SIGNING_SECRET = environ.get("SLACK_SIGNING_SECRET")
SLACK_OAUTH_TOKEN = environ.get("SLACK_OAUTH_TOKEN")
SLACK_VERIFICATION_TOKEN = environ.get("SLACK_VERIFICATION_TOKEN")
SLACK_PORT = environ.get("SLACK_PORT", 3000)
OPENAI_API_KEY = environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = environ.get("PINECONE_API_KEY")
PINECONE_NAMESPACE = environ.get("PINECONE_NAMESPACE", "ReadTheDocs")
PINECONE_ENV = environ.get("PINECONE_ENV")
PINECONE_INDEX = environ.get("PINECONE_INDEX")
SERPER_API_KEY = environ.get("SERPER_API_KEY")
LOGLEVEL = environ.get("LOG_LEVEL", "INFO").upper()

# Configure logger. To get JSON serialization, set serialize=True.
# See https://loguru.readthedocs.io/en/stable/ for info on Loguru features.
logger.remove(0) # remove the default handler configuration
logger.add(sys.stderr, level=LOGLEVEL, serialize=False)


# `this` is a pointer to the module object instance itself.
this = sys.modules[__name__]

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

if this.PINECONE_API_KEY is None:
    logger.info("Config: Pinecone environment variables not set")
else:
    if None in [this.PINECONE_NAMESPACE, this.PINECONE_ENV, this.PINECONE_INDEX]:
        logger.info("Config: Pinecone environment variables not set, unable to run")
        raise SystemExit(1)
    else:
        logger.info("Config: Pinecone environment variables are set")
