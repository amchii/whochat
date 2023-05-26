import functools
import json
import os
import pathlib
import re
import shutil
import tempfile
import threading
import time
from datetime import datetime
from typing import Dict, List, Union, overload
from urllib import request

import psutil

from ._comtypes import client as com_client
from .abc import CWechatRobotABC, RobotEventABC, RobotEventSinkABC
from .logger import logger
from .utils import guess_wechat_base_directory, guess_wechat_user_by_paths

_robot_local = threading.local()


# 保证每个线程的COM对象独立
def get_robot_object(com_id) -> CWechatRobotABC:
    if not hasattr(_robot_local, "robot_object"):
        setattr(_robot_local, "robot_object", com_client.CreateObject(com_id))
    return getattr(_robot_local, "robot_object")


def get_robot_event(com_id) -> RobotEventABC:
    if not hasattr(_robot_local, "robot_event"):
        setattr(_robot_local, "robot_event", com_client.CreateObject(com_id))
    return getattr(_robot_local, "robot_event")


def auto_start(func):
    @functools.wraps(func)
    def wrapper(self: "WechatBot", *args, **kwargs):
        self.start_robot_service()
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.exception(e)

    return wrapper


class WechatBot:
    def __init__(
        self,
        wx_pid,
        robot_object_id: str,
        robot_event_id: str = None,
        wechat_version=None,
    ):
        self.wx_pid = int(wx_pid)
        self._robot_object_id = robot_object_id
        self._robot_event_id = robot_event_id
        self.started = False
        self.user_info = {}
        self.event_connection = None

        self._base_directory = None
        self.image_hook_path = None
        self.voice_hook_path = None
        self.wechat_version = wechat_version

    @property
    def robot(self):
        return get_robot_object(self._robot_object_id)

    @property
    def robot_event(self):
        return get_robot_event(self._robot_event_id)

    def __enter__(self):
        self.start_robot_service()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_robot_service()

    def start_robot_service(self):
        if self.started:
            return True
        result = self.robot.CStartRobotService(
            self.wx_pid,
        )
        if result == 0:
            self.started = True
            if self.wechat_version:
                self.change_wechat_ver(self.wechat_version)
                logger.info(f"更改微信版本号为: {self.wechat_version}")
        return not result

    def stop_robot_service(self):
        if not self.started:
            return True
        result = self.robot.CStopRobotService(
            self.wx_pid,
        )
        if result == 0:
            self.started = False
        return not result

    @property
    def base_directory(self):
        if not self._base_directory:
            return self.get_base_directory()
        return self._base_directory

    def get_base_directory(self):
        p = psutil.Process(pid=self.wx_pid)
        base_directory = guess_wechat_base_directory([f.path for f in p.open_files()])
        self._base_directory = base_directory
        return base_directory

    @overload
    def send_image(self, wx_id, img_path) -> int:
        ...

    @auto_start
    def send_image(self, wx_id, img_path):
        path = pathlib.Path(img_path)
        if not path.is_absolute():
            base_dir = self.image_hook_path or self.base_directory
            path = pathlib.Path(base_dir).joinpath(path)

        # BUG: (20220821)图片文件名如果有多个"."的话不能成功发送, 所以复制到临时文件进行发送
        if "." in path.stem:
            with tempfile.TemporaryDirectory() as td:
                temp_path = os.path.join(td, os.urandom(5).hex() + path.suffix)
                shutil.copy(path, temp_path)
                return self.robot.CSendImage(self.wx_pid, wx_id, temp_path)

        return self.robot.CSendImage(self.wx_pid, wx_id, str(path))

    @overload
    def send_text(self, wx_id, text) -> int:
        ...

    @auto_start
    def send_text(self, wx_id, text):
        return self.robot.CSendText(self.wx_pid, wx_id, text)

    @overload
    def send_file(self, wx_id, filepath) -> int:
        ...

    @auto_start
    def send_file(self, wx_id, filepath):
        path = pathlib.Path(filepath)
        if not path.is_absolute():
            path = pathlib.Path(self.base_directory).joinpath(path)

        return self.robot.CSendFile(self.wx_pid, wx_id, str(path))

    @overload
    def send_article(
        self, wxid: str, title: str, abstract: str, url: str, imgpath: str
    ):
        ...

    @auto_start
    def send_article(
        self, wxid: str, title: str, abstract: str, url: str, imgpath: str
    ):
        return self.robot.CSendArticle(self.wx_pid, wxid, title, abstract, url, imgpath)

    @overload
    def send_card(self, wxid: str, shared_wxid: str, nickname: str) -> int:
        ...

    @auto_start
    def send_card(self, wxid: str, shared_wxid: str, nickname: str):
        return self.robot.CSendCard(self.wx_pid, wxid, shared_wxid, nickname)

    @overload
    def send_at_text(
        self,
        chatroom_id: str,
        at_wxids: Union[str, List[str]],
        text: str,
        auto_nickname: bool = True,
    ) -> int:
        ...

    @auto_start
    def send_at_text(
        self,
        chatroom_id: str,
        at_wxids: Union[str, List[str]],
        text: str,
        auto_nickname: bool = True,
    ):
        return self.robot.CSendAtText(
            self.wx_pid, chatroom_id, at_wxids, text, auto_nickname
        )

    @overload
    def get_friend_list(self) -> List[Dict]:
        ...

    @auto_start
    def get_friend_list(self):
        return [
            dict(item)
            for item in (
                self.robot.CGetFriendList(
                    self.wx_pid,
                )
                or []
            )
        ]

    @overload
    def get_wx_user_info(self, wxid: str):
        ...

    @auto_start
    def get_wx_user_info(self, wxid: str):
        return json.loads(self.robot.CGetWxUserInfo(self.wx_pid, wxid))

    @property
    def wxid(self):
        return self.get_self_info()["wxId"]

    @property
    def self_path(self):
        return os.path.join(self.base_directory, str(self.wx_pid))

    @overload
    def get_self_info(self, refresh=False) -> Dict:
        ...

    @auto_start
    def get_self_info(self, refresh=False):
        if refresh or not self.user_info:
            self.user_info = json.loads(
                self.robot.CGetSelfInfo(
                    self.wx_pid,
                )
            )
        return self.user_info

    @overload
    def check_friend_status(self, wxid: str) -> int:
        ...

    @auto_start
    def check_friend_status(self, wxid: str):
        return self.robot.CCheckFriendStatus(self.wx_pid, wxid)

    @overload
    def get_com_work_path(self) -> int:
        ...

    @auto_start
    def get_com_work_path(self):
        return self.robot.CGetComWorkPath(
            self.wx_pid,
        )

    @overload
    def start_receive_message(self, port: int) -> int:
        ...

    @auto_start
    def start_receive_message(self, port: int):
        """
        开始接收消息
        :param port: 端口， port为0则使用COM Event推送
        """
        return self.robot.CStartReceiveMessage(self.wx_pid, port)

    @overload
    def stop_receive_message(self) -> int:
        ...

    @auto_start
    def stop_receive_message(self):
        return self.robot.CStopReceiveMessage(
            self.wx_pid,
        )

    @overload
    def get_chat_room_member_ids(self, chatroom_id: str) -> List:
        ...

    @auto_start
    def get_chat_room_member_ids(self, chatroom_id: str):
        wx_ids_str: str = self.robot.CGetChatRoomMembers(self.wx_pid, chatroom_id)[1][1]
        wx_ids = wx_ids_str.split("^G")
        return wx_ids

    @overload
    def get_chat_room_member_nickname(self, chatroom_id: str, wxid: str) -> str:
        ...

    @auto_start
    def get_chat_room_member_nickname(self, chatroom_id: str, wxid: str):
        return self.robot.CGetChatRoomMemberNickname(self.wx_pid, chatroom_id, wxid)

    def get_chat_room_members(self, chatroom_id: str) -> List[dict]:
        """
        获取群成员id及昵称信息

        [
            {
                "wx_id": "",
                "nickname": ""
            }
        ]
        """
        results = []
        for wx_id in self.get_chat_room_member_ids(chatroom_id):
            results.append(
                {
                    "wx_id": wx_id,
                    "nickname": self.get_chat_room_member_nickname(chatroom_id, wx_id),
                }
            )
        return results

    @overload
    def add_friend_by_wxid(self, wxid: str, message: str) -> int:
        ...

    @auto_start
    def add_friend_by_wxid(self, wxid: str, message: str):
        return self.robot.CAddFriendByWxid(self.wx_pid, wxid, message)

    @overload
    def search_contact_by_net(self, keyword: str) -> List[Dict]:
        ...

    @auto_start
    def search_contact_by_net(self, keyword: str):
        return [
            dict(item) for item in self.robot.CSearchContactByNet(self.wx_pid, keyword)
        ]

    @overload
    def add_brand_contact(self, public_id: str) -> int:
        ...

    @auto_start
    def add_brand_contact(self, public_id: str):
        return self.robot.CAddBrandContact(self.wx_pid, public_id)

    @overload
    def change_wechat_ver(self, version: str) -> int:
        ...

    @auto_start
    def change_wechat_ver(self, version: str):
        return self.robot.CChangeWeChatVer(self.wx_pid, version)

    @overload
    def send_app_msg(self, wxid: str, app_id: str) -> int:
        ...

    @auto_start
    def send_app_msg(self, wxid: str, app_id: str):
        return self.robot.CSendAppMsg(self.wx_pid, wxid, app_id)

    @overload
    def delete_user(self, wxid: str) -> int:
        ...

    @auto_start
    def delete_user(self, wxid: str):
        return self.robot.CDeleteUser(self.wx_pid, wxid)

    @overload
    def is_wx_login(self) -> int:
        ...

    @auto_start
    def is_wx_login(self) -> int:
        return self.robot.CIsWxLogin(
            self.wx_pid,
        )

    @overload
    def get_db_handles(self) -> List[Dict]:
        ...

    @auto_start
    def get_db_handles(self):
        return [dict(item) for item in self.robot.CGetDbHandles(self.wx_pid)]

    @overload
    def register_event(self, event_sink: RobotEventSinkABC) -> int:
        ...

    @auto_start
    def register_event(self, event_sink: RobotEventSinkABC):
        if self.event_connection:
            self.event_connection.__del__()
        self.event_connection = com_client.GetEvents(self.robot_event, event_sink)
        self.robot_event.CRegisterWxPidWithCookie(
            self.wx_pid, self.event_connection.cookie
        )

    @overload
    def get_wechat_ver(self) -> str:
        ...

    @auto_start
    def get_wechat_ver(self) -> str:
        return self.robot.CGetWeChatVer()

    @overload
    def hook_voice_msg(self, savepath: str) -> Union[int, str]:
        ...

    @auto_start
    def hook_voice_msg(self, savepath: str) -> Union[int, str]:
        p = pathlib.Path(savepath)
        if not p.is_absolute():
            p = pathlib.Path.home().joinpath(p)
        result = self.robot.CHookVoiceMsg(self.wx_pid, str(p))
        if result == 0:
            self.voice_hook_path = str(p)
            return self.voice_hook_path
        return result

    @overload
    def unhook_voice_msg(self) -> int:
        ...

    @auto_start
    def unhook_voice_msg(self):
        return self.robot.CUnHookVoiceMsg(self.wx_pid)

    @overload
    def hook_image_msg(self, savepath: str) -> Union[int, str]:
        ...

    @auto_start
    def hook_image_msg(self, savepath: str) -> Union[int, str]:
        p = pathlib.Path(savepath)
        if not p.is_absolute():
            p = pathlib.Path.home().joinpath(p)
        result = self.robot.CHookImageMsg(self.wx_pid, str(p))
        if result == 0:
            self.image_hook_path = str(p)
            return self.image_hook_path
        return result

    @overload
    def unhook_image_msg(self) -> int:
        ...

    @auto_start
    def unhook_image_msg(self):
        return self.robot.CUnHookImageMsg(self.wx_pid)

    @overload
    def open_browser(self, url: str) -> int:
        ...

    @auto_start
    def open_browser(self, url: str):
        return self.robot.COpenBrowser(self.wx_pid, url)

    @overload
    def get_history_public_msg(self, public_id: str, offset: str = "") -> List:
        ...

    @auto_start
    def get_history_public_msg(self, public_id: str, offset: str = ""):
        """
        获取公众号历史消息

        Args:
            offset (str, optional): 起始偏移，为空的话则从新到久获取十条，该值可从返回数据中取得
        """
        r = self.robot.CGetHistoryPublicMsg(self.wx_pid, public_id, offset)
        try:
            msgs = json.loads(r[0])
        except (IndexError, json.JSONDecodeError) as e:
            logger.exception(e)
            return []
        return msgs

    @overload
    def forward_message(self, wxid: str, msgid: int) -> int:
        ...

    @auto_start
    def forward_message(self, wxid: str, msgid: int):
        """
        转发消息

        Args:
            wxid (str): 消息接收人
            msgid (int): 消息id
        """
        return self.robot.CForwardMessage(self.wx_pid, wxid, msgid)

    @overload
    def get_qrcode_image(
        self,
    ) -> bytes:
        ...

    @auto_start
    def get_qrcode_image(
        self,
    ) -> bytes:
        """
        获取二维码，同时切换到扫码登陆

        Returns:
            bytes
                二维码bytes数据.
        You can convert it to image object,like this:
        >>> from io import BytesIO
        >>> from PIL import Image
        >>> buf = wx.GetQrcodeImage()
        >>> image = Image.open(BytesIO(buf)).convert("L")
        >>> image.save('./qrcode.png')
        """
        return self.robot.CGetQrcodeImage(self.wx_pid)

    @overload
    def get_a8_key(self, url: str) -> str:
        ...

    @auto_start
    def get_a8_key(self, url: str):
        """
        获取A8Key

        Args:
            url (str): 公众号文章链接
        """
        r = self.robot.CGetA8Key(self.wx_pid, url)
        try:
            result = json.loads(r[0])
        except (IndexError, json.JSONDecodeError) as e:
            logger.exception(e)
            return ""
        return result

    @overload
    def send_xml_msg(self, wxid: str, xml: str, img_path: str) -> int:
        ...

    @auto_start
    def send_xml_msg(self, wxid: str, xml: str, img_path: str) -> int:
        """
        发送原始xml消息

        Returns:
            int: 0表示成功
        """
        return self.robot.CSendXmlMsg(self.wx_pid, wxid, xml, img_path)

    @overload
    def logout(self) -> int:
        ...

    @auto_start
    def logout(self) -> int:
        """
        登出

        Returns:
            int: 0表示成功
        """
        return self.robot.CLogout(self.wx_pid)

    @overload
    def get_transfer(self, wxid: str, transactionid: str, transferid: int) -> int:
        ...

    @auto_start
    def get_transfer(self, wxid: str, transactionid: str, transferid: int) -> int:
        """
        收款

        Args:
            wxid : str
                转账人wxid.
            transcationid : str
                从转账消息xml中获取.
            transferid : str
                从转账消息xml中获取.

        Returns:
            int
                成功返回0，失败返回非0值.
        """
        return self.robot.CGetTransfer(self.wx_pid, wxid, transactionid, transferid)

    @overload
    def send_emotion(self, wxid: str, img_path: str) -> int:
        ...

    @auto_start
    def send_emotion(self, wxid: str, img_path: str) -> int:
        return self.robot.CSendEmotion(self.wx_pid, wxid, img_path)

    @overload
    def get_msg_cdn(self, msgid: int) -> str:
        ...

    @auto_start
    def get_msg_cdn(self, msgid: int) -> str:
        """
        下载图片、视频、文件等

        Returns:
            str
                成功返回文件路径，失败返回空字符串.
        """
        return self.robot.CGetMsgCDN(self.wx_pid, msgid)

    def prevent_revoke(self, rel_path: str, hold_time: int = 120):
        """
        防止文件被删除
        通过打开文件来阻止微信将撤回的文件删除，仅Windows可用

        :param rel_path: 相对微信数据目录的路径，如微信目录为"C:\\Users\\foo\\Documents\\WeChat Files"，
                         `rel_path`为"foo.txt", 则实际文件路径为"C:\\Users\\foo\\Documents\\WeChat Files\\foo.txt"
        :param hold_time: 持续时间，秒，默认为微信撤回时间
        """
        full_path = os.path.join(self.base_directory, rel_path)
        start = time.perf_counter()
        if not os.path.isfile(full_path):
            tmp_file_path = full_path + ".wxtmp"
            if not os.path.exists(tmp_file_path):
                logger.error(
                    f"'{full_path}' is not a file and it's tmp file {tmp_file_path} not exists"
                )
                return 1

            while not os.path.isfile(full_path):
                time.sleep(0.1)
                if time.perf_counter() > start + hold_time:
                    logger.warning("File has been revoked")
                    return 1

        def hold():
            logger.info(f"Try to open file {full_path} to prevent the deletion.")
            with open(full_path, "rb"):
                while not time.perf_counter() > start + hold_time:
                    time.sleep(1)
            logger.info(f"Opened file {full_path} closed.")

        t = threading.Thread(
            target=hold,
        )
        t.start()
        return 0


class WechatBotFactoryMetaclass(type):
    _robot: CWechatRobotABC
    _robot_object_id: str
    _robot_event_id: str

    @property
    def robot(cls):
        return get_robot_object(cls._robot_object_id)

    @property
    def robot_event(cls):
        return get_robot_event(cls._robot_event_id)

    @property
    def robot_pid(cls) -> int:
        return cls.robot.CStopRobotService(0)


class WechatBotFactory(metaclass=WechatBotFactoryMetaclass):
    """
    单例
    """

    _instances: Dict[int, "WechatBot"] = {}
    _robot_object_id = "WeChatRobot.CWeChatRobot"
    _robot_event_id = "WeChatRobot.RobotEvent"

    @classmethod
    def get(cls, wx_pid) -> "WechatBot":
        if wx_pid not in cls._instances:
            wechat_version = os.environ.get(
                "WHOCHAT_WECHAT_VERSION"
            ) or cls.get_latest_wechat_version(fill=".99")
            bot = WechatBot(
                wx_pid,
                cls._robot_object_id,
                cls._robot_event_id,
                wechat_version=wechat_version,
            )
            cls._instances[wx_pid] = bot
        return cls._instances[wx_pid]

    @classmethod
    def exit(cls):
        logger.info("卸载注入的dll...")
        for instance in cls._instances.values():
            instance.stop_robot_service()

    @classmethod
    def get_we_chat_ver(cls) -> str:
        return cls.robot.CGetWeChatVer()

    @classmethod
    def start_wechat(cls) -> int:
        return cls.robot.CStartWeChat()

    @classmethod
    def list_wechat(cls) -> List[dict]:
        results = []
        for process in psutil.process_iter():
            if process.name().lower() == "wechat.exe":
                files = [f.path for f in process.open_files()]
                results.append(
                    {
                        "pid": process.pid,
                        "started": datetime.fromtimestamp(
                            process.create_time()
                        ).isoformat(),
                        "status": process.status(),
                        "wechat_user": guess_wechat_user_by_paths(files),
                        "base_directory": guess_wechat_base_directory(files),
                    }
                )
        return results

    @classmethod
    def get_robot_pid(cls):
        return cls.robot_pid

    @classmethod
    def kill_robot(cls):
        bot_pid = cls.robot_pid
        logger.info(f"尝试结束CWeChatRobot进程: pid {bot_pid}")
        try:
            psutil.Process(bot_pid).kill()
            logger.info("OK")
        except psutil.Error as e:
            logger.warning(e, exc_info=True)

    @classmethod
    def register_events(cls, wx_pids, event_sink: RobotEventSinkABC):
        connection = com_client.GetEvents(cls.robot_event, event_sink)
        for wx_pid in wx_pids:
            cls.robot_event.CRegisterWxPidWithCookie(wx_pid, connection.cookie)

    @classmethod
    def get_current_dir(cls):
        return os.getcwd()

    @classmethod
    def get_latest_wechat_version(cls, fill: str = None):
        logger.info("获取微信最新版本号...")
        with request.urlopen(
            request.Request(
                "https://pc.weixin.qq.com/?lang=zh_CN",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
                },
                method="GET",
            )
        ) as fp:
            html = fp.read().decode()
        m = re.search(r"download-version\">(.*?)</span>", html)
        if not m:
            logger.warning("获取微信最新版本号异常")
            return
        version = m.group(1)
        if fill:
            version = version + fill
        logger.info(f"微信最新版本号：{version}")
        return version
