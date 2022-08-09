from .bot_helper import BotRpcHelper


def register_rpc_methods(use_async=True):
    if use_async:
        BotRpcHelper.register_as_async_rpc_methods()
    else:
        BotRpcHelper.register_as_rpc_methods()
