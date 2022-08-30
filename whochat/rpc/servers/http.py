import json

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from jsonrpcserver import async_dispatch

from whochat.rpc.docs import make_docs

app = FastAPI(title="微信机器人RPC接口文档", description="HTTP和Websocket均使用JSON-RPC2.0进行函数调用")


@app.get(
    "/",
    name="点击查看已有的RPC接口",
    description=f"```json{json.dumps(make_docs(), indent=4, ensure_ascii=False)}```",
)
async def index():
    return RedirectResponse("/docs")


@app.get("/rpc_api_docs")
async def rpc_docs():
    return make_docs()


@app.post(
    "/",
    name="RPC调用接口",
    description="""```$ curl -X POST http://localhost:5000 -d '{"jsonrpc": "2.0", "method": "start_robot_service", "params": [23472], "id": 1}'```""",
)
async def rpc(request: Request):
    data = await request.body()
    result = await async_dispatch(data)
    return Response(result)
