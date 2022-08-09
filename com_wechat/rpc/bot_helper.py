import asyncio
import functools
import inspect
from concurrent.futures import ThreadPoolExecutor

from jsonrpcserver import Success, method

from com_wechat.bot import WechatBot

thread_pool_executor = ThreadPoolExecutor(max_workers=4)


class BotRpcHelper:
    bot_rpc_methods = {
        WechatBot.start_robot_service,
        WechatBot.stop_robot_service,
        WechatBot.start_receive_message,
        WechatBot.stop_receive_message,
        WechatBot.get_wx_user_info,
        WechatBot.send_text,
        WechatBot.send_image,
        WechatBot.send_file,
        WechatBot.send_card,
        WechatBot.send_article,
        WechatBot.send_app_msg,
        WechatBot.send_at_text,
        WechatBot.search_contact_by_net,
        WechatBot.get_friend_list,
        WechatBot.get_self_info,
        WechatBot.get_chat_room_members,
        WechatBot.add_friend_by_wxid,
        WechatBot.add_brand_contact,
        WechatBot.get_we_chat_ver,
        WechatBot.is_wx_login,
        WechatBot.delete_user,
    }

    @classmethod
    def rpc_method(cls, func):
        cls.bot_rpc_methods.add(func)
        return func

    @classmethod
    def register_as_rpc_methods(cls):
        from com_wechat.bot import WechatBotFactory

        for _rpc_method in cls.bot_rpc_methods:

            @method(name=_rpc_method.__name__)
            @functools.wraps(_rpc_method)
            def generic_func(wx_pid, *args, **kwargs):
                bot = WechatBotFactory.get(wx_pid)
                return Success(functools.partial(_rpc_method, bot, *args, **kwargs))

    @classmethod
    def register_as_async_rpc_methods(cls):
        import comtypes

        from com_wechat.bot import WechatBotFactory

        def factory(func):
            def _func(*args, **kwargs):
                comtypes.CoInitialize()
                r = func(*args, **kwargs)
                comtypes.CoUninitialize()
                return r

            @functools.wraps(func)
            async def generic_func(wx_pid, *args, **kwargs):
                bot = WechatBotFactory.get(wx_pid)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    thread_pool_executor,
                    functools.partial(_func, bot, *args, **kwargs),
                )
                return Success(result)

            return generic_func

        for _rpc_method in cls.bot_rpc_methods:
            method(name=_rpc_method.__name__)(factory(_rpc_method))


_docs = []


def make_docs():
    if _docs:
        return _docs
    for rpc_method in BotRpcHelper.bot_rpc_methods:
        s = inspect.signature(rpc_method)
        name = rpc_method.__name__
        description = rpc_method.__doc__
        params = [
            {"name": "wx_pid", "default": None, "required": True, "annotation": None}
        ]

        for param in s.parameters.values():
            if param.name == "self":
                continue
            params.append(
                {
                    "name": param.name,
                    "default": None if param.default is param.empty else param.default,
                    "required": param.default is param.empty,
                    "annotation": None
                    if param.annotation is param.empty
                    else str(param.annotation),
                }
            )
        _docs.append({"name": name, "description": description, "params": params})
    return _docs
