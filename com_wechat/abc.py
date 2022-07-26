import typing

DictIterable = typing.Iterable[typing.Tuple[str, typing.Any]]


class CWechatRobot:
    """Com Wechat实现的接口"""

    def CStartRobotService(self, wx_pid: int) -> int:
        ...

    def CStopRobotService(self, wx_pid: int) -> int:
        ...

    def CSendImage(self, wx_pid: int, wxid: str, imgpath: str) -> int:
        ...

    def CSendText(self, wx_pid: int, wxid: str, text: str) -> int:
        ...

    def CSendFile(self, wx_pid: int, wxid: str, filepath: str) -> int:
        ...

    def CSendArticle(
        self, wx_pid: int, wxid: str, title: str, abstract: str, url: str, imgpath: str
    ) -> int:
        ...

    def CSendCard(self, wx_pid: int, wxid: str, shared_wxid: str, nickname: str) -> int:
        ...

    def CSendAtText(
        self,
        wx_pid: int,
        chatroomid: str,
        at_wxids: typing.Union[str, typing.List[str]],
        text: str,
        auto_nickname: bool = True,
    ) -> int:
        ...

    def CGetFriendList(
        self,
        wx_pid: int,
    ) -> DictIterable:
        ...

    def CGetFriendListString(self, wx_pid: int):
        ...

    def CGetWxUserInfo(self, wx_pid: int, wxid: str) -> str:  # json
        ...

    def CGetSelfInfo(self, wx_pid: int) -> str:  # json
        ...

    def CCheckFriendStatus(self, wx_pid: int, wxid: str):
        """当前测试不是无痕检测"""
        ...

    def CGetComWorkPath(self, wx_pid: int) -> str:
        ...

    def CStartReceiveMessage(self, wx_pid: int, port: int) -> int:
        """向指定TCP端口发送接收到的消息, 消息结构参考`ReceiveMsgStruct`"""
        ...

    def CStopReceiveMessage(self, wx_pid: int) -> int:
        ...

    def CGetChatRoomMembers(self, wx_pid: int, chatroomid: str) -> DictIterable:
        ...

    def CGetDbHandles(self, wx_pid: int) -> DictIterable:
        ...

    def CExecuteSQL(self, wx_pid: int, handle: int, sql: str) -> list:
        ...

    def CBackupSQLiteDB(self, wx_pid: int, handle: int, savepath: str) -> int:
        ...

    def CVerifyFriendApply(self, wx_pid: int, v3: str, v4: str) -> int:
        ...

    def CAddFriendByWxid(self, wx_pid: int, wxid: str, message: str) -> int:
        ...

    def CAddFriendByV3(self, wx_pid: int, v3: str, message: str) -> int:
        ...

    def CGetWeChatVer(self) -> str:
        ...

    def CStartWeChat(self) -> int:
        ...

    def CSearchContactByNet(self, wx_pid: int, keyword: str) -> DictIterable:
        ...

    def CAddBrandContact(self, wx_pid: int, public_id: str) -> int:
        """添加公众号"""
        ...

    def CHookVoiceMsg(self, wx_pid: int, savepath: str) -> int:
        ...

    def CUnHookVoiceMsg(self, wx_pid: int) -> int:
        ...

    def CHookImageMsg(self, wx_pid: int, savepath: str) -> int:
        ...

    def CUnHookImageMsg(self, wx_pid: int) -> int:
        ...

    def CChangeWeChatVer(self, wx_pid: int, version: str) -> int:
        ...

    def CSendAppMsg(self, wx_pid: int, wxid: str, app_id: str) -> int:
        """发送小程序"""
        ...

    def CDeleteUser(self, wx_pid: int, wxid: str) -> int:
        ...

    def CIsWxLogin(self, wx_pid: int) -> int:
        ...

    def CEditRemark(self, wx_pid: int, wxid: str, remark: str):
        ...

    def CSetChatRoomName(self, wx_pid: int, chatroomid: str, name: str):
        ...

    def CSetChatRoomAnnouncement(self, wx_pid: int, chatroomid: str, announcement: str):
        ...

    def CSetChatRoomSelfNickname(self, wx_pid: int, chatroomid: str, nickname: str):
        ...

    def CGetChatRoomMemberNickname(self, wx_pid: int, chatroomid: str, wxid: str):
        ...

    def CDelChatRoomMember(self, wx_pid: int, chatroomid: str, wxids: list[str]):
        ...

    def CAddChatRoomMember(self, wx_pid: int, chatroomid: str, wxids: list[str]):
        ...
