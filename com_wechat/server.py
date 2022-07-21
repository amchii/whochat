import socket
import socketserver
import threading
import typing
from ctypes import Structure, c_wchar, sizeof, wintypes
from queue import Full, Queue

import pythoncom

from .bot import WechatBot, wechatbot
from .logger import logger


class ReceiveMsgStruct(Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("is_send_msg", wintypes.DWORD),
        ("sender", c_wchar * 80),
        ("wxid", c_wchar * 80),
        ("message", c_wchar * 0x1000B),
        ("filepath", c_wchar * 260),
        ("time", c_wchar * 30),
    ]

    @classmethod
    def from_bytes(cls, data: bytes) -> "ReceiveMsgStruct":
        return cls.from_buffer_copy(data)

    def to_dict(self):
        return {attname: getattr(self, attname) for attname, _ in self._fields_}


class ReceiveMsgHandler(socketserver.BaseRequestHandler):
    timeout = 3
    msg_struct_cls = ReceiveMsgStruct
    server: "WechatReceiveMsgServer"
    request: socket.socket

    def setup(self) -> None:
        self.request.settimeout(self.timeout)

    def handle(self) -> None:
        pythoncom.CoInitialize()
        try:
            data = self.request.recv(1024)
            struct_size = sizeof(ReceiveMsgStruct)
            while len(data) < struct_size:
                data += self.request.recv(1024)

            msg = self.msg_struct_cls.from_bytes(data)
            self._handle(msg, self.server.bot)
        except OSError as e:
            logger.exception(e)
            return
        finally:
            self.request.sendall(b"200 OK")
            pythoncom.CoUninitialize()

    def _handle(self, msg: ReceiveMsgStruct, bot: typing.Optional[WechatBot] = None):
        pass


class StoreReceiveMsgHandler(ReceiveMsgHandler):
    def __init__(self, request, client_address, server, queue: Queue):
        self.queue = queue
        super(StoreReceiveMsgHandler, self).__init__(request, client_address, server)

    def _handle(self, msg: ReceiveMsgStruct, bot: typing.Optional[WechatBot] = None):
        try:
            self.queue.put(msg, timeout=1)
        except Full:
            logger.warning(f"消息队列<size: {self.queue.maxsize}>已满")


class WechatReceiveMsgServer(socketserver.ThreadingTCPServer):
    """
    Com接口不支持指定IP
    """

    bot_cls = wechatbot

    def __init__(
        self,
        port: int,
        RequestHandlerClass: typing.Callable[..., ReceiveMsgHandler],
        **kwargs,
    ):
        self.port = port
        super().__init__(("127.0.0.1", port), RequestHandlerClass, **kwargs)

    @property
    def bot(self):
        return self.bot_cls()

    def serve_forever(self, poll_interval=0.5) -> None:
        with self.bot:
            self.bot.start_receive_message(self.port)
            super().serve_forever(poll_interval)

    def finish_request(self, request, client_address) -> None:
        self.RequestHandlerClass(request, client_address, self)


class WechatStoreReceiveMsgServer(WechatReceiveMsgServer):
    RequestHandlerClass: typing.Callable[..., StoreReceiveMsgHandler]

    def __init__(
        self,
        port: int,
        queue: Queue,
        RequestHandlerClass: typing.Callable[..., StoreReceiveMsgHandler],
        **kwargs,
    ):
        self.port = port
        self.queue = queue
        super().__init__(port, RequestHandlerClass, **kwargs)

    def finish_request(self, request, client_address) -> None:
        self.RequestHandlerClass(request, client_address, self, self.queue)

    def serve_forever_in_thread(self, poll_interval=0.5, daemon=True):
        t = threading.Thread(target=self.serve_forever, args=(poll_interval,))
        t.setDaemon(daemon)
        t.start()
        return t


if __name__ == "__main__":
    from .utils import get_free_port

    port = get_free_port()
    queue = Queue(maxsize=1000)
    store_server = WechatStoreReceiveMsgServer(port, queue, StoreReceiveMsgHandler)
    store_server.serve_forever_in_thread()
    while True:
        msg = queue.get()
        print(msg)
