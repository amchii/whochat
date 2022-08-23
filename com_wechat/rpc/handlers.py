import asyncio
import dataclasses
import functools
import inspect
import logging
import typing
from concurrent.futures import ThreadPoolExecutor

import comtypes
import schedule
from jsonrpcserver import InvalidParams, Success, methods

from com_wechat.bot import WechatBot

logger = logging.getLogger("whochat")

thread_pool_executor = ThreadPoolExecutor(
    max_workers=4,
    initializer=comtypes.CoInitializeEx,
    initargs=(comtypes.COINIT_APARTMENTTHREADED,),
)


class BotRpcHelper:
    bot_methods = {
        method.__name__: method
        for method in [
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
            WechatBot.get_chat_room_member_ids,
            WechatBot.get_chat_room_member_nickname,
            WechatBot.get_chat_room_members,
            WechatBot.add_friend_by_wxid,
            WechatBot.add_brand_contact,
            WechatBot.get_we_chat_ver,
            WechatBot.is_wx_login,
            WechatBot.delete_user,
            WechatBot.get_db_handles,
        ]
    }
    rpc_methods = {}
    async_rpc_methods = {}

    @classmethod
    def make_rpc_methods(cls):
        if cls.rpc_methods:
            return cls.rpc_methods

        from com_wechat.bot import WechatBotFactory

        for name, function in cls.bot_methods.items():

            @functools.wraps(function)
            def generic_func(wx_pid, *args, **kwargs):
                bot = WechatBotFactory.get(wx_pid)
                return Success(functools.partial(function, bot, *args, **kwargs))

            cls.rpc_methods[name] = generic_func
        return cls.rpc_methods

    @classmethod
    def make_async_rpc_methods(cls):
        if cls.async_rpc_methods:
            return cls.async_rpc_methods

        from com_wechat.bot import WechatBotFactory

        def factory(func):
            @functools.wraps(func)
            async def generic_func(wx_pid, *args, **kwargs):
                bot = WechatBotFactory.get(wx_pid)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    thread_pool_executor,
                    functools.partial(func, bot, *args, **kwargs),
                )
                return Success(result)

            return generic_func

        for name, function in cls.bot_methods.items():
            cls.async_rpc_methods[name] = factory(function)
        return cls.async_rpc_methods


@dataclasses.dataclass
class BotJob:
    """

    {
        "name": "",
        "unit": "days",
        "every": 1,
        "at": "12:00:00",
        "do": {
            "func": "",
            "args": []
        },
        "description": "",
        "tags": ""
    }
    """

    name: str
    unit: str
    every: int
    at: str
    do: dict
    description: str = None
    tags: list[str] = dataclasses.field(default_factory=list)
    _job_func: typing.Callable = dataclasses.field(init=False, default=None)

    def __post_init__(self):
        func_name, func_args = self.do["func"], self.do["args"]
        self._job_func = functools.partial(
            BotRpcHelper.make_rpc_methods()[func_name], *func_args
        )

    @property
    def job_func(self):
        return self._job_func

    def as_dict(self):
        return {
            "name": self.name,
            "unit": self.unit,
            "every": self.every,
            "at": self.at,
            "do": self.do,
            "description": self.description,
            "tags": self.tags,
        }


class BotScheduler:
    def __init__(self):
        self.jobs: dict[str, "BotJob"] = {}

    async def schedule_a_job(
        self,
        name: str,
        unit: str,
        every: int,
        at: str,
        do: dict,
        description=None,
        tags=None,
    ):
        """
        {
            "name": "Greet",
            "unit": "days",
            "every": 1,
            "at": "08:00:00",
            "do": {
                "func": "send_text",
                "args": [12314, "wxid_foo", "Morning!"]
            },
            "description": "",
            "tags": ["tian"]
        }
        参见 https://schedule.readthedocs.io/en/stable/examples.html
        :param name: 任务名
        :param unit: 单位，seconds, minutes, hours, days, weeks, monday, tuesday, wednesday, thursday, friday, saturday, sunday
        :param every: 每<unit>
        :param at:  For daily jobs -> HH:MM:SS or HH:MM
                    For hourly jobs -> MM:SS or :MM
                    For minute jobs -> :SS
        :param do: 执行的方法，func: 方法名, args: 参数列表
        :param description: 描述
        :param tags: 标签，总会添加任务名作为标签
        """
        try:
            job = BotJob(name, unit, every, at, do, description, tags or [])
            assert job.name not in self.jobs
            self.jobs[job.name] = job
            schedule_job = schedule.every(job.every)
            schedule_job.unit = job.unit
            schedule_job.at(job.at).do(job.job_func).tags(*job.tags, job.name)
        except AssertionError:
            raise InvalidParams(f"任务<{name}>已存在")
        except Exception as e:
            raise InvalidParams(f"参数错误: {str(e)}")

    async def cancel_job(self, tag):
        """
        取消任务
        :param tag: 标签名
        """
        self.jobs.pop(tag, None)
        schedule.clear(tag=tag)

    async def list_jobs(self) -> dict[str, dict]:
        """列出所有任务"""
        return {name: job.as_dict() for name, job in self.jobs.items()}

    def get_rpc_methods(self) -> dict[str, typing.Callable]:
        return {
            method.__name__: method
            for method in [self.schedule_a_job, self.cancel_job, self.list_jobs]
        }


default_bot_scheduler = BotScheduler()

_docs = []


def make_docs():
    if _docs:
        return _docs
    for name, rpc_method in BotRpcHelper.bot_methods.items():
        s = inspect.signature(rpc_method)
        description = rpc_method.__doc__
        params = [
            {
                "name": "wx_pid",
                "default": None,
                "required": True,
            }
        ]

        for param in s.parameters.values():
            if param.name == "self":
                continue
            params.append(
                {
                    "name": param.name,
                    "default": None if param.default is param.empty else param.default,
                    "required": param.default is param.empty,
                }
            )
        _docs.append({"name": name, "description": description, "params": params})

    for name, rpc_method in default_bot_scheduler.get_rpc_methods().items():
        s = inspect.signature(rpc_method)
        description = rpc_method.__doc__
        params = []
        for param in s.parameters.values():
            params.append(
                {
                    "name": param.name,
                    "default": None if param.default is param.empty else param.default,
                    "required": param.default is param.empty,
                }
            )
        _docs.append({"name": name, "description": description, "params": params})

    return _docs


def register_rpc_methods():
    rpc_methods = BotRpcHelper.make_async_rpc_methods()
    methods.global_methods.update(rpc_methods)
    methods.global_methods.update(default_bot_scheduler.get_rpc_methods())
