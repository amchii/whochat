import logging

logger = logging.getLogger("wechat")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
