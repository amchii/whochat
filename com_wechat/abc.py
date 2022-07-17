import typing

DictIterable = typing.Iterable[typing.Tuple[str, typing.Any]]


class CWechatRobot:
    """Com Wechat实现的接口"""

    def CStartRobotService(self) -> int:
        ...

    def CStartRobotServiceByWxPid(self, wx_pid: int) -> int:
        ...

    def CStopRobotService(self) -> int:
        ...

    def CStopRobotServiceByWxPid(self, wx_pid: int) -> int:
        ...

    def CSendImage(self, wxid: str, imgpath: str) -> int:
        ...

    def CSendText(self, wxid: str, text: str) -> int:
        ...

    def CSendFile(self, wxid: str, filepath: str) -> int:
        ...

    def CSendArticle(
        self, wxid: str, title: str, abstract: str, url: str, imgpath: str
    ) -> int:
        ...

    def CSendCard(self, wxid: str, shared_wxid: str, nickname: str) -> int:
        ...

    def CSendAtText(
        self,
        chatroomid: str,
        at_wxids: typing.Union[str, typing.List[str]],
        text: str,
        auto_nickname: bool = True,
    ) -> int:
        ...

    def CGetFriendList(
        self,
    ) -> DictIterable:
        ...

    def CGetFriendListString(self):
        ...

    def CGetWxUserInfo(self, wxid: str) -> str:  # json
        ...

    def CGetSelfInfo(self) -> str:  # json
        ...

    def CCheckFriendStatus(self, wxid: str):
        """当前测试不是无痕检测"""
        ...

    def CGetComWorkPath(self) -> str:
        ...

    def CStartReceiveMessage(self, port: int) -> int:
        """向指定TCP端口发送接收到的消息, 消息结构参考`ReceiveMsgStruct`"""
        ...

    def CStopReceiveMessage(self) -> int:
        ...

    def CGetChatRoomMembers(self, chatroomid: str) -> DictIterable:
        ...

    def CGetDbHandles(self) -> DictIterable:
        ...

    def CExecuteSQL(self, handle: int, sql: str) -> list:
        ...

    def CBackupSQLiteDB(self, handle: int, savepath: str) -> int:
        ...

    def CVerifyFriendApply(self, v3: str, v4: str) -> int:
        ...

    def CAddFriendByWxid(self, wxid: str, message: str) -> int:
        ...

    def CAddFriendByV3(self, v3: str, message: str) -> int:
        ...

    def CGetWeChatVer(self) -> str:
        ...

    def CStartWeChat(self) -> int:
        ...

    def CSearchContactByNet(self, keyword: str) -> DictIterable:
        ...

    def CAddBrandContact(self, public_id: str) -> int:
        """添加公众号"""
        ...

    def CHookVoiceMsg(self, savepath: str) -> int:
        ...

    def CUnHookVoiceMsg(self) -> int:
        ...

    def CHookImageMsg(self, savepath: str) -> int:
        ...

    def CUnHookImageMsg(self) -> int:
        ...

    def CChangeWeChatVer(self, version: str) -> int:
        ...

    def CSendAppMsg(self, wxid: str, app_id: str) -> int:
        """发送小程序"""
        ...

    def CDeleteUser(self, wxid: str) -> int:
        ...

    def CIsWxLogin(self) -> int:
        ...
