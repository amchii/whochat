import signal
from collections import defaultdict

from .logger import logger


class Signal:
    _signal_handlers = defaultdict(set)
    signalled = False

    @classmethod
    def register(cls, signum, func):
        if not cls.signalled:
            cls.signal()
        assert callable(func)
        cls._signal_handlers[signum].add(func)

    @classmethod
    def register_sigint(cls, func):
        logger.info(f"注册SIGINT信号处理程序: {func.__qualname__}")
        cls.register(signal.SIGINT, func)

    @classmethod
    def unregister(cls, signum, func):
        cls._signal_handlers[signum].remove(func)

    @classmethod
    def handler(cls, signum, frame):
        logger.info(f"接收到信号: {signal.strsignal(signum)}")
        for _handler in cls._signal_handlers[signum]:
            try:
                _handler()
            except Exception as e:
                logger.error(f"信号处理程序出现错误: {_handler}")
                logger.exception(e)

    @classmethod
    def signal(cls):
        signal.signal(signal.SIGINT, cls.handler)
        cls.signalled = True
