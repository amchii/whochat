import json
import logging
import socket
import socketserver
import typing
from ctypes import Structure, c_wchar, sizeof, wintypes

import pythoncom
import win32com.client
import win32com.util

from .abc import CWechatRobot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wechat")


class Wechat:
    def __init__(self):
        self.robot: CWechatRobot = win32com.client.Dispatch("WeChatRobot.CWeChatRobot")

    def __enter__(self):
        self.start_robot_service()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_robot_service()

    def start_robot_service(self):
        return self.robot.CStartRobotService()

    def start_robot_service_by_pid(self, wx_pid):
        return self.robot.CStartRobotServiceByWxPid(wx_pid)

    def stop_robot_service(self):
        return self.robot.CStopRobotService()

    def stop_robot_service_by_wx_pid(self, wx_pid):
        return self.robot.CStopRobotServiceByWxPid(wx_pid)

    def send_image(self, wx_id, img_path):
        return self.robot.CSendImage(wx_id, img_path)

    def send_text(self, wx_id, text):
        return self.robot.CSendText(wx_id, text)

    def send_file(self, wx_id, filepath):
        return self.robot.CSendFile(wx_id, filepath)

    def send_article(
        self, wxid: str, title: str, abstract: str, url: str, imgpath: str
    ):
        return self.robot.CSendArticle(wxid, title, abstract, url, imgpath)

    def send_card(self, wxid: str, shared_wxid: str, nickname: str):
        return self.robot.CSendCard(wxid, shared_wxid, nickname)

    def send_at_text(
        self,
        chatroom_id: str,
        at_wxids: typing.Union[str, typing.List[str]],
        text: str,
        auto_nickname: bool = True,
    ):
        return self.robot.CSendAtText(chatroom_id, at_wxids, text, auto_nickname)

    def get_friend_list(self):
        return self.robot.CGetFriendList() or []

    def get_wx_user_info(self, wxid: str):
        return self.robot.CGetWxUserInfo(wxid)

    def get_self_info(self):
        return json.loads(self.robot.CGetSelfInfo())

    def check_friend_status(self, wxid: str):
        return self.robot.CCheckFriendStatus(wxid)

    def get_com_work_path(self):
        return self.robot.CGetComWorkPath()

    def start_receive_message(self, port: int):
        return self.robot.CStartReceiveMessage(port)

    def stop_receive_message(self):
        return self.robot.CStopReceiveMessage()

    def get_chat_room_members(self, chatroom_id: str):
        return self.robot.CGetChatRoomMembers(chatroom_id)

    def add_friend_by_wxid(self, wxid: str, message: str):
        return self.robot.CAddFriendByWxid(wxid, message)

    def get_we_chat_ver(self):
        return self.robot.CGetWeChatVer()

    def start_wechat(self):
        return self.robot.CStartWeChat()

    def search_contact_by_net(self, keyword: str):
        return self.robot.CSearchContactByNet(keyword)

    def add_brand_contact(self, public_id: str):
        return self.robot.CAddBrandContact(public_id)

    def change_we_chat_ver(self, version: str):
        return self.robot.CChangeWeChatVer(version)

    def send_app_msg(self, wxid: str, app_id: str):
        return self.robot.CSendAppMsg(wxid, app_id)

    def delete_user(self, wxid: str):
        return self.robot.CDeleteUser(wxid)

    def is_wx_login(self):
        return self.robot.CIsWxLogin()


class ReceiveMsgStruct(Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("is_send_msg", wintypes.DWORD),
        ("sender", c_wchar * 80),
        ("wxid", c_wchar * 80),
        ("message", c_wchar * 0x1000B),
        ("filepath", c_wchar * 260),
        ("time", c_wchar * 30),
    ]

    @classmethod
    def from_bytes(cls, data: bytes) -> "ReceiveMsgStruct":
        return cls.from_buffer_copy(data)

    def to_dict(self):
        return {attname: getattr(self, attname) for attname, _ in self._fields_}


class ReceiveMsgHandler(socketserver.BaseRequestHandler):
    timeout = 3
    msg_struct_cls = ReceiveMsgStruct

    def setup(self) -> None:
        self.request: socket.socket
        self.request.settimeout(self.timeout)

    def handle(self) -> None:
        pythoncom.CoInitialize()
        self.request: socket.socket
        try:
            data = self.request.recv(1024)
            struct_size = sizeof(ReceiveMsgStruct)
            while len(data) < struct_size:
                data += self.request.recv(1024)

            msg = self.msg_struct_cls.from_bytes(data)
            self._handle(msg)
        except OSError as e:
            logger.exception(e)
            return
        finally:
            pythoncom.CoUninitialize()

    def _handle(self, msg: ReceiveMsgStruct):
        pass
