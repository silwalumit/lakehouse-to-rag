import logging
import logging.config
import sys

from config.logging import LogSettings
from helpers.logging.formatters import JSONFormatter, PrettyFormatter


def setup_logger(settings: LogSettings):
    formatter = JSONFormatter if settings.format_ == "Json" else PrettyFormatter

    logging_config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "default": {
                "()": formatter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": sys.stdout,
                "level": settings.level,
            }
        },
        "root": {"level": settings.level, "handlers": ["console"]},
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "ERROR",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
