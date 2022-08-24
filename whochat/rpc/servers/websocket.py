import asyncio
import logging

import websockets
from jsonrpcserver import async_dispatch

from whochat.signals import Signal

logger = logging.getLogger("whochat")


async def dispatch_in_task(websocket, request):
    res = await async_dispatch(request)
    await websocket.send(res)


async def handler(websocket):
    while True:
        request = await websocket.recv()
        asyncio.create_task(dispatch_in_task(websocket, request))


async def run(host, port):
    stop_event = asyncio.Event()

    def shutdown():
        logger.info("正在停止微信机器人RPC websocket服务...")
        stop_event.set()

    Signal.register_sigint(shutdown)
    async with websockets.serve(handler, host, port):
        logger.info(f"运行微信机器人RPC websocket服务, 地址为<{host}:{port}>")
        await stop_event.wait()
