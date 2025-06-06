import logging
import coloredlogs
from typing import Any

TRACE_LEVEL: int = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


def trace(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kwargs)


logging.Logger.trace = trace  # type: ignore


def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(TRACE_LEVEL)

    fmt = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    coloredlogs.install(
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
