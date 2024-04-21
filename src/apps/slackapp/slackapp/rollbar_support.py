from os import path

import sherpa_ai.config as cfg
from flask import got_request_exception
from loguru import logger
from sherpa_ai.config import current_app_revision_from_file_or_git


ROLLBAR_IMPORTED = False
try:
    import rollbar
    import rollbar.contrib.flask

    ROLLBAR_IMPORTED = True
except Exception:
    pass


def enable_rollbar(flask_app):
    """
    Turns on Rollbar exception tracking if the runtime environment is appropriate.

    Returns True if Rollbar is enabled, False otherwise.
    """
    if (
        ROLLBAR_IMPORTED
        and cfg.ROLLBAR_ACCESS_TOKEN is not None
        and cfg.SHERPA_ENV
        in [
            "development",
            "production",
        ]
    ):
        logger.info(f"Enabling Rollbar in { cfg.SHERPA_ENV } environment")

        # Follow pattern in https://github.com/rollbar/rollbar-flask-example/blob/master/hello.py:
        with flask_app.app_context():
            rollbar.init(
                cfg.ROLLBAR_ACCESS_TOKEN,
                environment=cfg.SHERPA_ENV,
                code_version=current_app_revision_from_file_or_git(),
                # server root directory, makes tracebacks prettier
                root=path.dirname(path.realpath(__file__)),
                # flask already sets up logging so don't ask Rollbar to do it
                allow_logging_basic_config=False,
                scrub_fields=cfg.SENSITIVE_SETTINGS_AND_SECRETS,
            )

        # Send exceptions from `app` to rollbar, using flask's signal system.
        got_request_exception.connect(rollbar.contrib.flask.report_exception, flask_app)
        return True
    else:
        return False
