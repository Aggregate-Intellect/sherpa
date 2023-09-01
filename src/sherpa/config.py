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
LOG_LEVEL = environ.get("LOG_LEVEL", "INFO").upper()
DAILY_TOKEN_LIMIT = environ.get("DAILY_TOKEN_LIMIT") or 20000
TEMPRATURE = environ.get("TEMPRATURE") or 0
DAILY_LIMIT_REACHED_MESSAGE = environ.get("DAILY_LIMIT_REACHED_MESSAGE") or "I  for the inconvenience, but it seems that you have exceeded your daily token limit. As a result, you will need to try again after 24 hours. Thank you for your understanding."



# Configure logger. To get JSON serialization, set serialize=True.
# See https://loguru.readthedocs.io/en/stable/ for info on Loguru features.
logger.remove(0) # remove the default handler configuration
logger.add(sys.stderr, level=LOG_LEVEL, serialize=False)


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