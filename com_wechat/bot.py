import json
import typing
from datetime import datetime

from .utils import guess_wechat_user_by_path

try:
    import comtypes.client as com_client
except ImportError:
    com_client = None

import psutil

from .abc import CWechatRobot
from .logger import logger


class BaseWechatBot:
    """
    可以嵌套使用with语句:
    ```
        with bot:
            with bot:
                with bot:
                    do_something()
    ```
    """

    _enter_count = 0

    def __init__(self, wx_pid, bot: CWechatRobot):
        self.wx_pid = wx_pid
        self._robot = bot

    def __enter__(self):
        if self._enter_count <= 0:
            self._enter_count = 0
            self.start_robot_service()
        self._enter_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._enter_count -= 1
        if self._enter_count <= 0:
            self.stop_robot_service()

    def start_robot_service(self):
        return self._robot.CStartRobotService(
            self.wx_pid,
        )

    def stop_robot_service(self):
        return self._robot.CStopRobotService(
            self.wx_pid,
        )

    def send_image(self, wx_id, img_path):
        return self._robot.CSendImage(self.wx_pid, wx_id, img_path)

    def send_text(self, wx_id, text):
        return self._robot.CSendText(self.wx_pid, wx_id, text)

    def send_file(self, wx_id, filepath):
        return self._robot.CSendFile(self.wx_pid, wx_id, filepath)

    def send_article(
        self, wxid: str, title: str, abstract: str, url: str, imgpath: str
    ):
        return self._robot.CSendArticle(
            self.wx_pid, wxid, title, abstract, url, imgpath
        )

    def send_card(self, wxid: str, shared_wxid: str, nickname: str):
        return self._robot.CSendCard(self.wx_pid, wxid, shared_wxid, nickname)

    def send_at_text(
        self,
        chatroom_id: str,
        at_wxids: typing.Union[str, typing.List[str]],
        text: str,
        auto_nickname: bool = True,
    ):
        return self._robot.CSendAtText(
            self.wx_pid, chatroom_id, at_wxids, text, auto_nickname
        )

    def get_friend_list(self):
        return (
            self._robot.CGetFriendList(
                self.wx_pid,
            )
            or []
        )

    def get_wx_user_info(self, wxid: str):
        return self._robot.CGetWxUserInfo(self.wx_pid, wxid)

    def get_self_info(self):
        return json.loads(
            self._robot.CGetSelfInfo(
                self.wx_pid,
            )
        )

    def check_friend_status(self, wxid: str):
        return self._robot.CCheckFriendStatus(self.wx_pid, wxid)

    def get_com_work_path(self):
        return self._robot.CGetComWorkPath(
            self.wx_pid,
        )

    def start_receive_message(self, port: int):
        return self._robot.CStartReceiveMessage(self.wx_pid, port)

    def stop_receive_message(self):
        return self._robot.CStopReceiveMessage(
            self.wx_pid,
        )

    def get_chat_room_members(self, chatroom_id: str):
        return self._robot.CGetChatRoomMembers(self.wx_pid, chatroom_id)

    def add_friend_by_wxid(self, wxid: str, message: str):
        return self._robot.CAddFriendByWxid(self.wx_pid, wxid, message)

    def search_contact_by_net(self, keyword: str):
        return self._robot.CSearchContactByNet(self.wx_pid, keyword)

    def add_brand_contact(self, public_id: str):
        return self._robot.CAddBrandContact(self.wx_pid, public_id)

    def change_we_chat_ver(self, version: str):
        return self._robot.CChangeWeChatVer(self.wx_pid, version)

    def send_app_msg(self, wxid: str, app_id: str):
        return self._robot.CSendAppMsg(self.wx_pid, wxid, app_id)

    def delete_user(self, wxid: str):
        return self._robot.CDeleteUser(self.wx_pid, wxid)

    def is_wx_login(self):
        return self._robot.CIsWxLogin(
            self.wx_pid,
        )


class WechatBotMetaclass(type):
    _robot: CWechatRobot
    _robot_com_id: str

    @property
    def robot(cls):
        if cls._robot is None:
            cls._robot = com_client.CreateObject(cls._robot_com_id)
        return cls._robot

    @property
    def bot_pid(cls) -> int:
        return cls.robot.CStopRobotService(0)


class WechatBot(BaseWechatBot, metaclass=WechatBotMetaclass):
    """
    单例
    """

    _instances = {}
    _robot = None
    _robot_com_id = "WeChatRobot.CWeChatRobot"

    def __new__(cls, wx_pid=None, *args, **kwargs) -> "BaseWechatBot":
        if wx_pid not in cls._instances:
            cls._instances[wx_pid] = BaseWechatBot(wx_pid=wx_pid, bot=cls.robot)
        return cls._instances[wx_pid]

    @classmethod
    def get_we_chat_ver(cls) -> str:
        return cls.robot.CGetWeChatVer()

    @classmethod
    def start_wechat(cls) -> int:
        return cls.robot.CStartWeChat()

    @classmethod
    def list_wechat(cls) -> list[dict]:
        results = []
        for process in psutil.process_iter():
            if process.name().lower() == "wechat.exe":
                results.append(
                    {
                        "pid": process.pid,
                        "started": datetime.fromtimestamp(process.create_time()),
                        "status": process.status(),
                        "wechat_user": guess_wechat_user_by_path(
                            process.open_files()[-1].path
                        ),
                    }
                )
        return results

    @classmethod
    def kill_robot(cls):
        bot_pid = cls.bot_pid
        logger.info(f"尝试结束CWeChatRobot进程: PID{bot_pid}")
        try:
            psutil.Process(bot_pid).kill()
        except psutil.Error as e:
            logger.warning(e, exc_info=True)
