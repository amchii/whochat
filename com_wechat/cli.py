import click


@click.group(
    name="wechat-bot",
)
def wechat_bot():
    """
    微信机器人

    使用<子命令> --help查看使用说明
    """


@wechat_bot.command()
def list_wechat():
    """列出当前运行的微信进程"""
    from com_wechat.bot import WechatBotFactory

    s = ""
    for r in WechatBotFactory.list_wechat():
        s += f"PID: {r['pid']}" + "\n"
        s += f"启动时间: {r['started'].isoformat()}" + "\n"
        s += f"运行状态: {r['status']}" + "\n"
        s += f"用户名: {r['wechat_user']}" + "\n"
        s += "---\n"
    click.echo(s)


@wechat_bot.command()
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

    from com_wechat.websocket import WechatWebsocketServer

    if not wx_pids:
        raise click.BadArgumentUsage("请指定至少一个微信进程PID")

    async def main():
        server = WechatWebsocketServer(wx_pids=wx_pids, ws_host=host, ws_port=port)
        await server.serve()

    asyncio.run(main())


@wechat_bot.command()
def show_rpc_docs():
    """
    列出RPC接口
    """
    import json

    from com_wechat.rpc.bot_helper import make_docs

    for doc in make_docs():
        click.echo(json.dumps(doc, ensure_ascii=False, indent=4))


@wechat_bot.command()
@click.option(
    "--host", "-h", default="localhost", show_default=True, help="Server host."
)
@click.option("--port", "-p", default=9002, show_default=True, help="Server port")
def serve_rpc_ws(host, port):
    """
    运行微信机器人RPC服务(JSON-RPC2.0), 使用Websocket
    """
    import asyncio

    from com_wechat.rpc.bot_helper import BotRpcHelper
    from com_wechat.rpc.servers.websocket import run

    BotRpcHelper.register_as_async_rpc_methods()

    asyncio.run(run(host, port))


@wechat_bot.command()
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

    from com_wechat.rpc.bot_helper import BotRpcHelper
    from com_wechat.rpc.servers.http import app

    BotRpcHelper.register_as_async_rpc_methods()
    uvicorn.run(app, host=host, port=port)
