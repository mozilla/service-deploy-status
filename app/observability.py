# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import logging
from logging.config import dictConfig


LOGGER = logging.getLogger(__name__)


def log_settings(app):
    settings = {
        key: val
        for key, val in app.config.items()
        if key.startswith("APP") or key in ["DEBUG", "TESTING"]
    }

    # If we're in a local dev environment log the settings one per line. Otherwise
    # log them all in one line as a JSON blob.
    if app.config["APP_ENVIRONMENT"] == "local":
        for key, val in settings.items():
            app.logger.info("%s: %s", key, repr(val))
    else:
        app.logger.info(json.dumps(settings))


def setup_logging(env, logging_level):
    # Configure Python logging to send all messages to loguru via the InterceptHandler
    logging_config = {
        "version": 1,
        "disabled_existing_handlers": True,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S +0000",
            },
            "mozlog": {
                "()": "dockerflow.logging.JsonLogFormatter",
                "logger_name": "app",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
            },
            "server": {
                "class": "logging.StreamHandler",
                "formatter": "mozlog",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "app": {"level": logging_level},
            "gunicorn": {"level": "WARNING"},
            "gunicorn.error": {"level": "WARNING"},
            "werkzeug": {"level": "WARNING"},
        },
        "root": {
            "handlers": ["server"],
            "level": "DEBUG",
        },
    }

    # If this is running in a local dev environment, switch the settings to something
    # more developer-friendly.
    if env == "local":
        logging_config["loggers"]["gunicorn"]["level"] = "DEBUG"
        logging_config["loggers"]["werkzeug"]["level"] = "DEBUG"
        logging_config["root"]["handlers"] = ["console"]

    dictConfig(logging_config)

    LOGGER.info("logging set up; environment=%s level=%s", env, logging_level)


def setup_metrics(config):
    pass
