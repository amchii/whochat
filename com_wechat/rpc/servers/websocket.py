import asyncio

import websockets
from jsonrpcserver import async_dispatch


async def handler(websocket):
    while True:
        request = await websocket.recv()
        await websocket.send(await async_dispatch(request))


async def run(host, port):
    async with websockets.serve(handler, host, port):
        await asyncio.Future()
