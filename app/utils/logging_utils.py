"""logging_utils.py

Logging functions for diagnostic purposes.
"""

import os

_LEVELS = {
    "silent": 0,
    "info": 1,
    "debug": 2,
    "verbose": 3,
}

_DEFAULT_LEVEL = "info"
_ENV_VAR = "HUMAN_CONTROLLER_LOG_LEVEL"


def _current_level_value():
    configured = os.environ.get(_ENV_VAR, _DEFAULT_LEVEL).strip().lower()
    return _LEVELS.get(configured, _LEVELS[_DEFAULT_LEVEL])


def log_at(level, message):
    if _current_level_value() < _LEVELS[level]:
        return

    print(message, flush=True)


def log_info(message):
    log_at("info", message)


def log_debug(message):
    log_at("debug", message)


def log_verbose(message):
    log_at("verbose", message)
