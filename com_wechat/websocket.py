import asyncio
import json

import websockets

from .logger import logger


class WechatWebsocketServer:
    def __init__(
        self,
        receive_msg_address: tuple[str, int],
        redirect_key=b"",
        ws_host=None,
        ws_port=9001,
        queue: asyncio.Queue = None,
        **kwargs,
    ):
        self.receive_msg_address = receive_msg_address
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.ws_server = None
        self.clients = set()
        self.extra_kwargs = kwargs
        self.redirect_key = redirect_key
        self.queue = queue or asyncio.Queue(maxsize=10)

        self.stop_receive_msg = False
        self.stop_broadcast = False

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
            await asyncio.Future()

    async def start_receive_msg(self, host, port, retry_wait=10):
        logger.info(f"开始运行微信消息接收服务，目标地址为：<{host}:{port}>")
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(self.redirect_key)
            await writer.drain()
            while not self.stop_receive_msg:
                data = await reader.readline()
                if not data:
                    raise BrokenPipeError
                try:
                    json.loads(data)
                except json.JSONDecodeError:
                    logger.warning("JSON数据解析失败")
                    continue
                if self.queue.full():
                    await self.queue.get()
                await self.queue.put(data)

        except OSError:
            logger.warning(f"接收消息失败，{retry_wait}秒后重试")
            await asyncio.sleep(retry_wait)
            return await self.start_receive_msg(host, port, retry_wait)

        logger.info("微信消息接收服务已停止")

    async def broadcast_received_msg(self):
        logger.info("开始向客户端广播接收到的微信消息")
        while not self.stop_broadcast:
            data = await self.queue.get()
            self.broadcast(data)
        logger.info("广播已停止")

    async def serve(self):
        websocket_task = asyncio.create_task(self.serve_websocket())
        receive_msg_task = asyncio.create_task(
            self.start_receive_msg(
                self.receive_msg_address[0], self.receive_msg_address[1]
            )
        )
        broadcast_task = asyncio.create_task(self.broadcast_received_msg())

        await websocket_task
        self.stop_broadcast = True
        self.stop_receive_msg = True
        await receive_msg_task
        await broadcast_task

    def broadcast(self, data):
        logger.info(f"广播消息：{data}")
        websockets.broadcast(self.clients, data)
