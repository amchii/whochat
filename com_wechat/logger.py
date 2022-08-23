import logging

logger = logging.getLogger("whochat")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
