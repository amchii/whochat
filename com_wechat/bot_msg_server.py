import json
import socket
import socketserver
import threading
import time
import typing
from collections import deque
from ctypes import Structure, c_wchar, sizeof, wintypes

import comtypes

from .bot import BaseWechatBot, WechatBot
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
    server: "WechatReceiveMsgTCPServer"
    request: socket.socket

    def setup(self) -> None:
        self.request.settimeout(self.timeout)

    def handle(self) -> None:
        comtypes.CoInitialize()
        try:
            data = self.request.recv(1024)
            struct_size = sizeof(ReceiveMsgStruct)
            while len(data) < struct_size:
                data += self.request.recv(1024)

            msg = self.msg_struct_cls.from_bytes(data)
            self._handle(msg, self.server.bot)
            self.request.sendall(b"200 OK")
        except OSError as e:
            logger.exception(e)
            return
        finally:
            comtypes.CoUninitialize()

    def _handle(
        self, msg: ReceiveMsgStruct, bot: typing.Optional[BaseWechatBot] = None
    ):
        pass


class WechatReceiveMsgTCPServer(socketserver.ThreadingTCPServer):
    """
    Com接口不支持指定IP
    """

    bot_cls = WechatBot

    def __init__(
        self,
        port: int,
        RequestHandlerClass: typing.Callable[..., ReceiveMsgHandler],
        wx_pid=None,
        **kwargs,
    ):
        self.wx_pid = wx_pid
        self.port = port
        super().__init__(("127.0.0.1", port), RequestHandlerClass, **kwargs)

    @property
    def bot(self):
        return self.bot_cls(wx_pid=self.wx_pid)

    def serve_forever(self, poll_interval=0.5) -> None:
        logger.info(f"开始运行微信消息接收服务，地址为：{self.server_address}")
        with self.bot:
            self.bot.start_receive_message(self.port)
            super().serve_forever(poll_interval)


class StoreReceiveMsgHandler(ReceiveMsgHandler):
    def __init__(
        self, request, client_address, server, queue: deque[dict], initial_data=b""
    ):
        self.dqueue = queue
        self.initial_data = initial_data
        super(StoreReceiveMsgHandler, self).__init__(request, client_address, server)

    def handle(self) -> None:
        data = self.initial_data
        comtypes.CoInitialize()
        try:
            while True:
                data += self.request.recv(1024)
                struct_size = sizeof(ReceiveMsgStruct)
                while len(data) < struct_size:
                    data += self.request.recv(1024)

                msg = self.msg_struct_cls.from_bytes(data)
                self._handle(msg, self.server.bot)
                data = b""
                self.request.sendall(b"200 OK")
        except OSError as e:
            logger.exception(e)
        finally:
            comtypes.CoUninitialize()

    def _handle(
        self, msg: ReceiveMsgStruct, bot: typing.Optional[BaseWechatBot] = None
    ):
        msg_dict = msg.to_dict()
        logger.debug(msg_dict)
        self.dqueue.append(msg_dict)


class WechatReceiveMsgRedirectTCPServer(WechatReceiveMsgTCPServer):
    RequestHandlerClass: typing.Callable[..., StoreReceiveMsgHandler]
    dqueue: deque[dict]

    def __init__(
        self,
        port: int,
        redirect_key=b"",
        RequestHandlerClass: typing.Callable[
            ..., StoreReceiveMsgHandler
        ] = StoreReceiveMsgHandler,
        **kwargs,
    ):
        self.port = port
        self.dqueue = deque(maxlen=100)
        # addr tuple -> socket client which need to redirect message
        self.redirects: set[socket.socket] = set()
        self.redirect_key = redirect_key
        assert len(self.redirect_key) <= 16
        super().__init__(port, RequestHandlerClass, **kwargs)
        logger.info(f"转发Key为: {self.redirect_key}")

    def finish_request(self, request, client_address) -> None:
        flag = request.recv(len(self.redirect_key))
        if flag == self.redirect_key:
            self.redirects.add(request)
            logger.info(f"已添加一个接受消息转发的客户端：{client_address}")
        else:
            self.RequestHandlerClass(
                request, client_address, self, self.dqueue, initial_data=flag
            )

    def shutdown_request(self, request) -> None:
        if request in self.redirects:
            return
        super().shutdown_request(request)

    def serve_forever_in_thread(self, poll_interval=0.5, daemon=True):
        def serve_in_thread():
            comtypes.CoInitialize()
            self.serve_forever(poll_interval)
            comtypes.CoUninitialize()

        t = threading.Thread(target=serve_in_thread)
        t.setDaemon(daemon)
        t.start()
        return t

    def keep_redirect(self):
        logger.info("开启转发服务")
        while True:
            if len(self.dqueue) != 0:
                msg = self.dqueue.popleft()
                data = json.dumps(msg).encode("utf-8") + b"\n"
                bad_requests = set()
                for redirect in self.redirects:
                    try:
                        redirect.sendall(data)
                    except Exception:
                        bad_requests.add(redirect)
                for bad_request in bad_requests:
                    self.redirects.remove(bad_request)
                    self.shutdown_request(bad_request)
                    logger.info("已移除一个接受消息转发的客户端")
            time.sleep(0.1)

    def serve(self):
        self.serve_forever_in_thread()
        self.keep_redirect()
