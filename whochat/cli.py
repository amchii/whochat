import os

import click

from whochat.rpc.handlers import register_rpc_methods


@click.group(
    name="whochat",
)
def whochat():
    """
    微信机器人

    使用<子命令> --help查看使用说明
    """


@whochat.command()
def list_wechat():
    """列出当前运行的微信进程"""
    from whochat.bot import WechatBotFactory

    s = ""
    for r in WechatBotFactory.list_wechat():
        s += f"PID: {r['pid']}" + "\n"
        s += f"启动时间: {r['started'].isoformat()}" + "\n"
        s += f"运行状态: {r['status']}" + "\n"
        s += f"用户名: {r['wechat_user']}" + "\n"
        s += "---\n"
    click.echo(s)


@whochat.command()
@click.option(
    "--host", "-h", default="localhost", show_default=True, help="Server host."
)
@click.option("--port", "-p", default=9001, show_default=True, help="Server port")
@click.argument("wx_pids", nargs=-1, type=int)
def serve_message_ws(host, port, wx_pids):
    """
    运行接收微信消息的Websocket服务

    WX_PIDS: 微信进程PID
    """
    import asyncio

    from whochat.messages.websocket import WechatWebsocketServer

    if not wx_pids:
        raise click.BadArgumentUsage("请指定至少一个微信进程PID")

    async def main():
        server = WechatWebsocketServer(wx_pids=wx_pids, ws_host=host, ws_port=port)
        await server.serve()

    asyncio.run(main())


@whochat.command()
def show_rpc_docs():
    """
    列出RPC接口

    \b
    whochat show-rpc-docs > docs.json
    """
    import json

    from whochat.rpc.handlers import make_docs

    click.echo(json.dumps(make_docs(), ensure_ascii=False, indent=4))


@whochat.command()
@click.option(
    "--host", "-h", default="localhost", show_default=True, help="Server host."
)
@click.option("--port", "-p", default=9002, show_default=True, help="Server port")
def serve_rpc_ws(host, port):
    """
    运行微信机器人RPC服务(JSON-RPC2.0), 使用Websocket
    """
    import asyncio

    from whochat.rpc.servers.websocket import run

    click.echo(f"PID: {os.getpid()}")
    register_rpc_methods()

    asyncio.run(run(host, port))


@whochat.command()
@click.option(
    "--host", "-h", default="localhost", show_default=True, help="Server host."
)
@click.option("--port", "-p", default=9002, show_default=True, help="Server port")
def serve_rpc_http(host, port):
    """
    运行微信机器人RPC服务(JSON-RPC2.0), 使用HTTP接口

    需要安装fastapi和uvicorn: `pip install fastapi uvicorn`
    """
    import uvicorn

    from whochat.rpc.servers.http import app

    register_rpc_methods()
    uvicorn.run(app, host=host, port=port)
