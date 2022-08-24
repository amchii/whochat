import asyncio
import dataclasses
import functools
import inspect
import logging
import time
import typing
from concurrent.futures import ThreadPoolExecutor

import comtypes
import schedule
from jsonrpcserver import InvalidParams, Success, methods

from whochat.bot import WechatBot
from whochat.signals import Signal

logger = logging.getLogger("whochat")

bot_executor = ThreadPoolExecutor(
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

        from whochat.bot import WechatBotFactory

        def factory(func):
            @functools.wraps(func)
            def generic_func(wx_pid, *args, **kwargs):
                bot = WechatBotFactory.get(wx_pid)
                _func = functools.partial(func, bot, *args, **kwargs)
                return Success(_func())

            return generic_func

        for name, function in cls.bot_methods.items():

            cls.rpc_methods[name] = factory(function)
        return cls.rpc_methods

    @classmethod
    def make_async_rpc_methods(cls):
        if cls.async_rpc_methods:
            return cls.async_rpc_methods

        from whochat.bot import WechatBotFactory

        def factory(func):
            @functools.wraps(func)
            async def generic_func(wx_pid, *args, **kwargs):
                bot = WechatBotFactory.get(wx_pid)
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    bot_executor,
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


scheduler_executor = ThreadPoolExecutor(
    max_workers=2,
    initializer=comtypes.CoInitializeEx,
    initargs=(comtypes.COINIT_APARTMENTTHREADED,),
)


class BotScheduler:
    def __init__(self, loop=None):
        self.jobs: dict[str, "BotJob"] = {}
        self._loop = loop
        self.executor = scheduler_executor
        self.scheduler = schedule.default_scheduler
        self.scheduled = False
        self.__shutdown = False

    @property
    def loop(self):
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        return self._loop

    def run(self):
        logger.info("开始运行任务消费线程")
        while not self.__shutdown:
            self.scheduler.run_pending()
            time.sleep(0.3)
        logger.info("任务消费线程已停止")

    def schedule(self):
        if self.scheduled:
            return
        self.scheduled = True
        Signal.register_sigint(self.shutdown)
        self.executor.submit(self.run)

    def shutdown(self):
        logger.info("正在取消所有任务...")
        self.__shutdown = True
        self._cancel_jobs()
        self.executor.shutdown(wait=False)

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
        self.schedule()
        try:
            job = BotJob(name, unit, every, at, do, description, tags or [])
            assert job.name not in self.jobs
            self.jobs[job.name] = job
            schedule_job = self.scheduler.every(job.every)
            schedule_job.unit = job.unit
            schedule_job.at(job.at).do(job.job_func).tag(*job.tags, job.name)
        except AssertionError:
            return InvalidParams(f"任务<{name}>已存在")
        except Exception as e:
            return InvalidParams(f"参数错误: {str(e)}")
        return Success()

    def _cancel_jobs(self, tag=None):
        if tag is None:
            self.jobs.clear()
        self.jobs.pop(tag, None)
        self.scheduler.clear(tag=tag)
        return Success()

    async def cancel_jobs(self, tag=None):
        """
        取消任务
        :param tag: 标签名
        """
        await self.loop.run_in_executor(
            self.executor, functools.partial(self._cancel_jobs, tag=tag)
        )
        return Success()

    async def list_jobs(self):
        """列出所有任务"""
        return Success({name: job.as_dict() for name, job in self.jobs.items()})

    def get_rpc_methods(self) -> dict[str, typing.Callable]:
        return {
            method.__name__: method
            for method in [self.schedule_a_job, self.cancel_jobs, self.list_jobs]
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