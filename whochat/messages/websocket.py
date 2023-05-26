import asyncio
import json
import logging
import re
import warnings
from collections import deque
from functools import partial
from typing import Awaitable, Callable, List

import websockets
import websockets.client
import websockets.server
from websockets.typing import Data

from whochat import _comtypes as comtypes
from whochat.abc import RobotEventSinkABC
from whochat.bot import WechatBotFactory
from whochat.signals import Signal
from whochat.utils import EventWaiter

logger = logging.getLogger("whochat")


class MessageEventStoreSink(RobotEventSinkABC):
    def __init__(self, deque_: deque):
        self.deque_ = deque_

    @staticmethod
    def _parse_extrainfo(extrainfo):
        extra = {"is_at_msg": False}
        android_windows_at_pattern = r"<atuserlist><!\[CDATA\[(.*?)\]\]></atuserlist>"
        m = re.search(android_windows_at_pattern, extrainfo)
        if not m:
            mac_at_pattern = r"<atuserlist>(.*?)</atuserlist>"
            m = re.search(mac_at_pattern, extrainfo)
        if m:
            extra["is_at_msg"] = True
            extra["at_user_list"] = m.group(1).split(",")
        m = re.search(r"<membercount>(\d+)</membercount>", extrainfo)
        if m:
            extra["member_count"] = int(m.group(1))
        return extra

    def OnGetMessageEvent(self, msg):
        if isinstance(msg, (list, tuple)):
            msg = msg[0]
        try:
            data = json.loads(msg)
            if "@chatroom" not in data["sender"]:
                data["extrainfo"] = None
            else:
                data["extrainfo"] = self._parse_extrainfo(data["extrainfo"])
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("接收消息错误: ")
            logger.exception(e)
            return
        logger.debug(f"收到消息: {data}")
        self.deque_.append(data)


class WechatMessageWebsocketServer:
    def __init__(
        self,
        wx_pids: List[int],
        ws_host: str = None,
        ws_port: int = 9001,
        queue: asyncio.Queue = None,
        welcome: bool = True,
        **kwargs,
    ):
        self.wx_pids = wx_pids
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.extra_kwargs = kwargs
        self.queue = queue or asyncio.Queue(maxsize=10)
        self.welcome = welcome

        self.ws_server = None
        self.clients = set()
        self._deque = deque(maxlen=self.queue.maxsize)
        self._event_waiter = EventWaiter(2)

        self._stop_broadcast = False
        self._stop_receive_msg = False
        self._stop_websocket = asyncio.Event()
        Signal.register_sigint(self.shutdown)

    async def handler(self, websocket):
        if websocket not in self.clients:
            logger.info(f"Accept connection from {websocket.remote_address}")
            self.clients.add(websocket)
            if self.welcome:
                await websocket.send("hello")
            await websocket.wait_closed()
            self.clients.remove(websocket)
            logger.info(f"Connection from {websocket.remote_address} was closed")

    async def serve_websocket(self):
        async with websockets.server.serve(
            self.handler, self.ws_host, self.ws_port, **self.extra_kwargs
        ) as ws_server:
            logger.info(f"开始运行微信Websocket服务，地址为：<{self.ws_host}:{self.ws_port}>")
            self.ws_server = ws_server
            async with ws_server:
                await self._stop_websocket.wait()
            logger.info("Websocket服务已停止")

    def _start_receive_msg(self, wx_pids):
        comtypes.CoInitialize()
        try:
            sink = MessageEventStoreSink(self._deque)
            for wx_pid in wx_pids:
                bot = WechatBotFactory.get(wx_pid)
                bot.start_robot_service()
                logger.info(bot.get_self_info())
                logger.info("开启Robot消息推送")
                bot.start_receive_message(0)
                bot.register_event(sink)
            self._event_waiter.create_handle()
            self._event_waiter.wait_forever()
        finally:
            comtypes.CoUninitialize()

    async def deque_to_queue(self):
        while not self._stop_receive_msg:
            try:
                e = self._deque.popleft()
                await self.queue.put(e)
            except IndexError:
                await asyncio.sleep(0.1)

    async def start_receive_msg(self):
        logger.info("开始运行微信消息接收服务")
        loop = asyncio.get_event_loop()
        loop.create_task(self.deque_to_queue())
        await loop.run_in_executor(None, partial(self._start_receive_msg, self.wx_pids))
        logger.info("微信消息接收服务已停止")

    def stop_websocket(self):
        self._stop_websocket.set()

    def stop_receive_msg(self):
        self._event_waiter.stop()
        self._stop_receive_msg = True
        for wx_pid in self.wx_pids:
            bot = WechatBotFactory.get(wx_pid)
            bot.stop_receive_message()
            bot.stop_robot_service()

    def stop_broadcast(self):
        self._stop_broadcast = True
        try:
            self.queue.put_nowait("bye")
        except asyncio.QueueFull:
            pass

    async def broadcast_received_msg(self):
        logger.info("开始向客户端广播接收到的微信消息")
        while not self._stop_broadcast:
            data = await self.queue.get()
            if not self._stop_broadcast:
                self.broadcast(json.dumps(data))
        logger.info("广播已停止")

    def broadcast(self, data):
        logger.debug(f"广播消息：{data}")
        websockets.broadcast(self.clients, data)

    def shutdown(self):
        logger.info("停止服务中...")
        self.stop_websocket()
        self.stop_broadcast()
        self.stop_receive_msg()

    async def serve(self):
        try:
            websocket_task = asyncio.create_task(self.serve_websocket())
            receive_msg_task = asyncio.create_task(self.start_receive_msg())
            broadcast_task = asyncio.create_task(self.broadcast_received_msg())

            await websocket_task
            await receive_msg_task
            await broadcast_task
        except Exception as e:
            logger.exception(e)
            raise


class WechatWebsocketServer(WechatMessageWebsocketServer):
    def __init__(self, *args, **kwargs):
        warnings.warn(" 'WechatWebsocketServer' 已更名为 'WechatMessageWebsocketServer'")
        super().__init__(*args, **kwargs)


class WechatMessageWebsocketClient:
    def __init__(
        self,
        ws_uri: str,
    ):
        self.ws_uri = ws_uri

    async def start_consumer(self, on_message: Callable[[Data], Awaitable]):
        logger.info("Starting message consumer...")
        async for websocket in websockets.client.connect(self.ws_uri):
            websocket: "websockets.client.WebSocketClientProtocol"
            logger.info(f"Websocket client bind on {websocket.local_address}")
            try:
                async for message in websocket:
                    await on_message(message)
            except websockets.ConnectionClosed:
                continue
