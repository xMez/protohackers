import logging
from typing import Any, Dict


logging_config: Dict[str, Any] = {
    "version": 1,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%H:%M:%S",
            "style": "%",
            "validate": True,
        }
    },
    "filters": {},
    "handlers": {
        "console": {
            "class": logging.StreamHandler,
            "formatter": "simple",
            "level": "DEBUG",
            "filters": [],
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "protohackers": {
            "level": "DEBUG",
            "propagate": 0,
            "filters": [],
            "handlers": [
                "console",
            ],
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": [
            "console",
        ],
    },
}
