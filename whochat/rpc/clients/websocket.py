import asyncio
import json
import logging
from collections import defaultdict
from functools import partial
from typing import Any, Dict

import websockets
import websockets.client
from jsonrpcclient import request as req

from whochat.rpc.handlers import make_rpc_methods

logger = logging.getLogger("whochat")

unset = object()


class Timeout(Exception):
    pass


class BotWebsocketRPCClient:
    def __init__(self, ws_uri):
        self.ws_uri = ws_uri
        self.send_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1)
        self._rpc_methods = make_rpc_methods()
        self._results = defaultdict(lambda: unset)
        self._current_request_id = None

    async def start_result_cleaner(self):
        logger.info("Starting result cleaner")
        while removable := len(self._results) - 100 > 0:
            logger.info(
                f"Current size of results: {len(self._results)}, will remove {removable} items"
            )
            for k in list(self._results.keys())[:removable]:
                self._results.pop(k, None)
            await asyncio.sleep(1)

    async def start_sender(
        self, websocket: "websockets.client.WebSocketClientProtocol"
    ):
        while not websocket.closed:
            request_dict = await self.send_queue.get()
            logger.debug(f"SEND: {request_dict}")
            try:
                await websocket.send(json.dumps(request_dict))
            except websockets.ConnectionClosed:
                await self.send_queue.put(request_dict)
                raise

    async def start_receiver(
        self, websocket: "websockets.client.WebSocketClientProtocol"
    ):
        async for message in websocket:
            logger.debug(f"RECV: {message}")
            try:
                response_dict = json.loads(message)
                if "result" in response_dict:
                    self._results[response_dict["id"]] = response_dict["result"]
                elif "error" in response_dict:
                    self._results[response_dict["id"]] = response_dict["error"]
                    logger.error(response_dict["error"])
            except json.JSONDecodeError:
                continue

    async def start_consumer(self):
        logger.info("Starting rpc client consumer")
        async for websocket in websockets.client.connect(self.ws_uri):
            websocket: "websockets.client.WebSocketClientProtocol"
            logger.info(f"Websocket client bind on {websocket.local_address}")
            gathered = asyncio.gather(
                self.start_receiver(websocket),
                self.start_sender(websocket),
            )
            try:
                await gathered
            except websockets.ConnectionClosedOK:
                logger.warning(
                    f"Websocket{websocket.local_address} closed",
                )
            except websockets.ConnectionClosedError:
                logger.warning(
                    f"Websocket{websocket.local_address} closed unexpectedly",
                )
            finally:
                gathered.cancel()

    def consume_in_background(self):
        asyncio.create_task(self.start_consumer())
        asyncio.create_task(self.start_result_cleaner())

    async def _send_and_recv(self, request):
        await self.send_queue.put(request)
        request_id = request["id"]
        while True:
            if self._results[request_id] is unset:
                await asyncio.sleep(0.1)
            else:
                return self._results[request_id]

    async def rpc_call(self, name: str, params, timeout):
        request = req(name, params)
        request_id = request["id"]
        self._current_request_id = request_id
        if timeout < 0:
            asyncio.create_task(self.send_queue.put(request))
            return request_id
        if timeout == 0:
            return await self._send_and_recv(request)
        else:
            try:
                return await asyncio.wait_for(self._send_and_recv(request), timeout)
            except asyncio.TimeoutError:
                raise Timeout(f"Timeout: rpc call timeout: {name}, params {params}")

    def __getattr__(self, item):
        def remote_func(*params, timeout=5):
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
