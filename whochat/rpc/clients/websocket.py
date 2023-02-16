import asyncio
import json
import logging
import time
from collections import defaultdict
from functools import partial
from typing import Any, Dict

import websockets
from jsonrpcclient import request as req
from websockets.legacy.client import WebSocketClientProtocol

from whochat.rpc.handlers import make_rpc_methods

logger = logging.getLogger("whochat")


class unset:  # noqa
    pass


class Timeout(Exception):
    pass


class BotWebsocketRPCClient:
    def __init__(self, ws_uri):
        self.ws_uri = ws_uri
        self.send_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1)
        self._rpc_methods = make_rpc_methods()
        self._results = defaultdict(lambda: unset)

    async def start_sender(self, websocket: WebSocketClientProtocol):
        while True:
            request_dict = await self.send_queue.get()
            logger.info(f"SEND: {request_dict}")
            await websocket.send(json.dumps(request_dict))

    async def start_receiver(self, websocket: WebSocketClientProtocol):
        while True:
            response = await websocket.recv()
            logger.info(f"RECV: {response}")
            try:
                response_dict = json.loads(response)
                if "result" in response_dict:
                    self._results[response_dict["id"]] = response_dict["result"]
                elif "error" in response_dict:
                    logger.error(response_dict["error"])
            except json.JSONDecodeError:
                pass

    async def start_consumer(self):
        async for websocket in websockets.connect(self.ws_uri):
            websocket: WebSocketClientProtocol
            try:
                await asyncio.gather(
                    self.start_receiver(websocket), self.start_sender(websocket)
                )
            except websockets.ConnectionClosed:
                pass

    async def rpc_call(self, name: str, params, timeout):
        request = req(name, params)
        request_id = request["id"]

        await self.send_queue.put(request)
        if timeout < 0:
            self._results.pop(request_id, None)
            return request_id
        elif timeout == 0:
            while True:
                if self._results[request_id] is unset:
                    await asyncio.sleep(0.1)
                else:
                    return self._results[request_id]
        else:
            start = time.perf_counter()
            while time.perf_counter() < start + timeout:
                if self._results[request_id] is unset:
                    await asyncio.sleep(0.1)
                else:
                    return self._results[request_id]
            raise Timeout(f"Timeout: rpc call timeout: {name}, params {params}")

    def __getattr__(self, item):
        def remote_func(*params, timeout=0):
            """
            :param params: 仅支持位置参数
            :param timeout: 超时时间。0: 阻塞等待返回结果, <0: 直接返回不等结果,  >0: 等待超时时间
            """
            return self.rpc_call(item, params, timeout)

        return remote_func


class OneBotWebsocketRPCClient:
    """For convenience"""

    def __init__(self, wx_pid, rpc_client: "BotWebsocketRPCClient"):
        self.wx_pid = wx_pid
        self.rpc_client = rpc_client

    def __getattr__(self, item):
        return partial(getattr(self.rpc_client, item), self.wx_pid)
