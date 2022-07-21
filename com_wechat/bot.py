import json
import typing

import win32com.client

from .abc import CWechatRobot


class WechatBot:
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

    def __init__(self, com_object="WeChatRobot.CWeChatRobot"):
        self._bot: CWechatRobot = win32com.client.Dispatch(com_object)

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
        return self._bot.CStartRobotService()

    def start_robot_service_by_pid(self, wx_pid):
        return self._bot.CStartRobotServiceByWxPid(wx_pid)

    def stop_robot_service(self):
        return self._bot.CStopRobotService()

    def stop_robot_service_by_wx_pid(self, wx_pid):
        return self._bot.CStopRobotServiceByWxPid(wx_pid)

    def send_image(self, wx_id, img_path):
        return self._bot.CSendImage(wx_id, img_path)

    def send_text(self, wx_id, text):
        return self._bot.CSendText(wx_id, text)

    def send_file(self, wx_id, filepath):
        return self._bot.CSendFile(wx_id, filepath)

    def send_article(
        self, wxid: str, title: str, abstract: str, url: str, imgpath: str
    ):
        return self._bot.CSendArticle(wxid, title, abstract, url, imgpath)

    def send_card(self, wxid: str, shared_wxid: str, nickname: str):
        return self._bot.CSendCard(wxid, shared_wxid, nickname)

    def send_at_text(
        self,
        chatroom_id: str,
        at_wxids: typing.Union[str, typing.List[str]],
        text: str,
        auto_nickname: bool = True,
    ):
        return self._bot.CSendAtText(chatroom_id, at_wxids, text, auto_nickname)

    def get_friend_list(self):
        return self._bot.CGetFriendList() or []

    def get_wx_user_info(self, wxid: str):
        return self._bot.CGetWxUserInfo(wxid)

    def get_self_info(self):
        return json.loads(self._bot.CGetSelfInfo())

    def check_friend_status(self, wxid: str):
        return self._bot.CCheckFriendStatus(wxid)

    def get_com_work_path(self):
        return self._bot.CGetComWorkPath()

    def start_receive_message(self, port: int):
        return self._bot.CStartReceiveMessage(port)

    def stop_receive_message(self):
        return self._bot.CStopReceiveMessage()

    def get_chat_room_members(self, chatroom_id: str):
        return self._bot.CGetChatRoomMembers(chatroom_id)

    def add_friend_by_wxid(self, wxid: str, message: str):
        return self._bot.CAddFriendByWxid(wxid, message)

    def get_we_chat_ver(self):
        return self._bot.CGetWeChatVer()

    def start_wechat(self):
        return self._bot.CStartWeChat()

    def search_contact_by_net(self, keyword: str):
        return self._bot.CSearchContactByNet(keyword)

    def add_brand_contact(self, public_id: str):
        return self._bot.CAddBrandContact(public_id)

    def change_we_chat_ver(self, version: str):
        return self._bot.CChangeWeChatVer(version)

    def send_app_msg(self, wxid: str, app_id: str):
        return self._bot.CSendAppMsg(wxid, app_id)

    def delete_user(self, wxid: str):
        return self._bot.CDeleteUser(wxid)

    def is_wx_login(self):
        return self._bot.CIsWxLogin()


class wechatbot(WechatBot):
    """
    单例
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = WechatBot(*args, **kwargs)
        return cls._instance
