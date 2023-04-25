import asyncio
import logging

import websockets.server
from jsonrpcserver import async_dispatch

from whochat.signals import Signal

logger = logging.getLogger("whochat")


async def dispatch_in_task(websocket, request):
    res = await async_dispatch(request)
    await websocket.send(res)


async def handler(websocket: "websockets.server.WebSocketServerProtocol"):
    logger.info(f"Accept connection from {websocket.remote_address}")
    while not websocket.closed:
        request = await websocket.recv()
        asyncio.create_task(dispatch_in_task(websocket, request))

    logger.info(f"Connection from {websocket.remote_address} was closed")


async def run(host, port):
    stop_event = asyncio.Event()

    def shutdown():
        logger.info("正在停止微信机器人RPC websocket服务...")
        stop_event.set()
        from whochat.bot import WechatBotFactory

        WechatBotFactory.exit()

    Signal.register_sigint(shutdown)
    async with websockets.server.serve(handler, host, port):
        logger.info(f"运行微信机器人RPC websocket服务, 地址为<{host}:{port}>")
        await stop_event.wait()
