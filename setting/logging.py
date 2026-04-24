import sys

from loguru import logger

from setting.config import app_config


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=app_config.log_level.upper(),
        backtrace=False,
        diagnose=False,
    )
