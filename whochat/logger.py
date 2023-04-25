import logging
from logging.handlers import RotatingFileHandler

from whochat.settings import settings

verbose_formatter = logging.Formatter(
    "[%(levelname)s] [%(name)s] %(asctime)s %(filename)s %(process)d %(message)s"
)

file_handler = RotatingFileHandler(
    settings.LOG_DIR.joinpath("whochat.log"),
    maxBytes=1024 * 1024,  # 1MB
    backupCount=10,
    encoding="utf-8",
)
file_handler.setFormatter(verbose_formatter)

logger = logging.getLogger("whochat")
logger.setLevel(settings.DEFAULT_LOG_LEVEL)
logger.addHandler(logging.StreamHandler())
logger.addHandler(file_handler)
