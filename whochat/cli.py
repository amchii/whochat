import logging
import os
from logging.handlers import RotatingFileHandler

import click

from whochat.rpc.handlers import register_rpc_methods
from whochat.utils import windows_only


@click.group(
    name="whochat",
)
@click.option(
    "--log-level",
    "-l",
    "log_level",
    default="info",
    show_default=True,
    help="日志等级, `debug`, `info`, `warn`, `error`",
)
@click.option("--log-file", "log_file", help="日志文件, 可以是相对路径")
def whochat(log_level: str, log_file):
    """
    微信机器人

    使用<子命令> --help查看使用说明
    """
    logger = logging.getLogger("whochat")
    logger.setLevel(log_level.upper())
    if log_file:
        abs_log_file = os.path.abspath(log_file)
        dirname = os.path.dirname(abs_log_file)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        assert os.path.isdir(dirname), f"{dirname}不存在或不是一个目录"
        file_handler = RotatingFileHandler(
            abs_log_file,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=10,
            encoding="utf-8",
        )
        verbose_formatter = logging.Formatter(
            "[%(levelname)s] [%(name)s] %(asctime)s %(filename)s %(process)d %(message)s"
        )
        file_handler.setFormatter(verbose_formatter)
        logger.addHandler(file_handler)


@whochat.command()
def version():
    """显示程序和支持微信的版本信息"""
    from whochat import __version__
    from whochat.ComWeChatRobot import __robot_commit_hash__, __wechat_version__

    s = ""
    s += f"WhoChat version: {__version__}\n"
    s += f"Supported WeChat version: {__wechat_version__}\n"
    s += f"Build ComWechatRobot's dll from: {__robot_commit_hash__}"
    click.echo(s)


@whochat.command()
@click.option("--unreg", "-R", is_flag=True, default=False, help="取消注册")
def regserver(unreg):
    """注册COM"""
    windows_only()
    from whochat.ComWeChatRobot import register, unregister

    if unreg:
        unregister()
    else:
        register()


@whochat.command()
def list_wechat():
    """列出当前运行的微信进程"""
    windows_only()

    from whochat.bot import WechatBotFactory

    s = ""
    for r in WechatBotFactory.list_wechat():
        s += f"PID: {r['pid']}" + "\n"
        s += f"启动时间: {r['started']}" + "\n"
        s += f"运行状态: {r['status']}" + "\n"
        s += f"用户名: {r['wechat_user']}" + "\n"
        s += "---\n"
    click.echo(s)


@whochat.command()
@click.option(
    "--host", "-h", default="localhost", show_default=True, help="Server host."
)
@click.option("--port", "-p", default=9001, show_default=True, help="Server port")
@click.option(
    "--welcome",
    default=True,
    type=bool,
    show_default=True,
    help="Respond 'hello' on client connect",
)
@click.argument("wx_pids", nargs=-1, type=int)
def serve_message_ws(host, port, welcome, wx_pids):
    """
    运行接收微信消息的Websocket服务

    WX_PIDS: 微信进程PID
    """
    windows_only()

    import asyncio

    from whochat.messages.websocket import WechatMessageWebsocketServer

    if not wx_pids:
        raise click.BadArgumentUsage("请指定至少一个微信进程PID")

    async def main():
        server = WechatMessageWebsocketServer(
            wx_pids=wx_pids, ws_host=host, ws_port=port, welcome=welcome
        )
        await server.serve()

    asyncio.run(main())


@whochat.command()
@click.option("--json", "json_", is_flag=True, default=False, help="JSON文档")
def show_rpc_docs(json_):
    """
    列出RPC接口

    \b
    whochat show-rpc-docs
    or
    whochat show-rpc-docs --json > api.json
    """
    import json

    from whochat.rpc.docs import make_docs, pretty_docs

    if json_:
        click.echo(json.dumps(make_docs(), ensure_ascii=False, indent=4))
    else:
        click.echo(pretty_docs())


@whochat.command()
@click.option(
    "--host", "-h", default="localhost", show_default=True, help="Server host."
)
@click.option("--port", "-p", default=9002, show_default=True, help="Server port")
def serve_rpc_ws(host, port):
    """
    运行微信机器人RPC服务(JSON-RPC2.0), 使用Websocket
    """
    windows_only()

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
    windows_only()

    import uvicorn

    from whochat.rpc.servers.http import app

    register_rpc_methods()
    uvicorn.run(app, host=host, port=port)
