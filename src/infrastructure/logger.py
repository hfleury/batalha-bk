"""Configures and sets up logging for the application."""

import logging
from typing import Any

import coloredlogs  # type: ignore

from src.config import settings


TRACE_LEVEL: int = 5

logging.addLevelName(TRACE_LEVEL, "TRACE")


def trace(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    """Logs a message with the custom TRACE level.

    This method is dynamically added to the logging.Logger class.

    Args:
        self: The logger instance.
        message: The message to log.
        *args: Variable argument list for message formatting.
        **kwargs: Keyword arguments for logging (e.g., exc_info).
    """
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kwargs)


logging.Logger.trace = trace  # type: ignore


def setup_logging() -> None:
    """Sets up the application's logging configuration.

    Configures the root logger to use `coloredlogs` for enhanced console output.
    """
    logger = logging.getLogger()
    log_level = getattr(logging, settings.log.log_level.upper())
    logger.setLevel(log_level)

    fmt = settings.log.log_format
    dateformat = settings.log.log_date_format
    level_styles = settings.log.level_styles
    field_styles = settings.log.field_styles
    formatter = logging.Formatter(fmt, datefmt=dateformat)

    if settings.log.should_install_coloredlogs:
        coloredlogs.install(  # type: ignore
            level=log_level,
            logger=logger,
            datefmt=dateformat,
            fmt=fmt,
            level_styles=level_styles or None,
            field_styles=field_styles or None,
        )
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
