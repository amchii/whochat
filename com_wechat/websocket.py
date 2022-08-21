import asyncio
import json
from collections import deque
from functools import partial

import comtypes
import comtypes.client
import websockets

from com_wechat.bot import WechatBotFactory

from .abc import RobotEventSinkABC
from .logger import logger
from .signals import Signal
from .utils import EventWaiter


class MessageEventStoreSink(RobotEventSinkABC):
    def __init__(self, deque_: deque):
        self.deque_ = deque_

    def OnGetMessageEvent(self, msg):
        data = dict(msg)
        logger.info(f"收到消息: {data}")
        self.deque_.append(data)


class WechatWebsocketServer:
    def __init__(
        self,
        wx_pids: list[int],
        ws_host: str = None,
        ws_port: int = 9001,
        queue: asyncio.Queue = None,
        **kwargs,
    ):
        self.wx_pids = wx_pids
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.extra_kwargs = kwargs
        self.queue = queue or asyncio.Queue(maxsize=10)

        self.ws_server = None
        self.clients = set()
        self._deque = deque(maxlen=self.queue.maxsize)
        self._event_waiter = EventWaiter(2)

        self._stop_broadcast = False
        self._stop_websocket = asyncio.Event()
        Signal.register_sigint(self.shutdown)

    async def handler(self, websocket):
        if websocket not in self.clients:
            self.clients.add(websocket)
            await websocket.send("hello")
            await websocket.wait_closed()
            self.clients.remove(websocket)

    async def serve_websocket(self):
        async with websockets.serve(
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
        while True:
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
        logger.info(f"广播消息：{data}")
        websockets.broadcast(self.clients, data)

    def shutdown(self):
        logger.info("停止服务中...")
        self.stop_websocket()
        self.stop_broadcast()
        self.stop_receive_msg()

    async def serve(self):
        websocket_task = asyncio.create_task(self.serve_websocket())
        receive_msg_task = asyncio.create_task(self.start_receive_msg())
        broadcast_task = asyncio.create_task(self.broadcast_received_msg())

        await websocket_task
        self.stop_broadcast()
        self.stop_receive_msg()
        await receive_msg_task
        await broadcast_task
