"""Configures and sets up logging for the application."""

import logging
from typing import Any

import coloredlogs  # type: ignore

TRACE_LEVEL: int = 5

# Add a custom logging level for TRACE, which is typically finer than DEBUG.
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
    logger.setLevel(TRACE_LEVEL)

    fmt = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    coloredlogs.install(  # type: ignore
        level=TRACE_LEVEL,
        logger=logger,
        fmt=fmt,
        level_styles={
            "trace": {"color": "magenta"},
            "debug": {"color": "blue"},
            "info": {"color": "green"},
            "warning": {"color": "yellow"},
            "error": {"color": "red"},
            "critical": {"color": "red", "bold": True},
        },
        field_styles={
            "asctime": {"color": "cyan"},
            "levelname": {"bold": True},
            "name": {"color": "white"},
        },
    )
