import logging
from logging.handlers import RotatingFileHandler

from whochat.settings import settings

verbose_formatter = logging.Formatter(
    "[%(levelname)s] [%(name)s] %(asctime)s %(filename)s %(process)d %(message)s"
)

logger = logging.getLogger("whochat")
logger.setLevel(settings.DEFAULT_LOG_LEVEL)
console_handler = logging.StreamHandler()
console_handler.setFormatter(verbose_formatter)
logger.addHandler(console_handler)

if settings.DEBUG:
    logger.setLevel(logging.DEBUG)
    file_handler = RotatingFileHandler(
        settings.DEV_LOG_DIR.joinpath("whochat.log"),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setFormatter(verbose_formatter)
    logger.addHandler(file_handler)
