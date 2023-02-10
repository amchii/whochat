from typing import Any, List, Sequence, Tuple, Union

DictIterable = Sequence[Tuple[str, Any]]
JsonStr = str


class CWechatRobotABC:
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
        at_wxids: Union[str, List[str]],
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

    def CDelChatRoomMember(self, wx_pid: int, chatroomid: str, wxids: List[str]):
        ...

    def CAddChatRoomMember(self, wx_pid: int, chatroomid: str, wxids: List[str]):
        ...

    def COpenBrowser(self, wx_pid: int, url: str):
        """
        打开内置浏览器
        """

    def CGetHistoryPublicMsg(
        self, wx_pid: int, public_id: str, offset: str = ""
    ) -> Tuple[JsonStr]:
        """
        获取公众号历史消息

        Args:
            offset (str, optional): 起始偏移，为空的话则从新到久获取十条，该值可从返回数据中取得.
        """

    def CForwardMessage(self, wx_pid: int, wxid: str, msgid: int):
        """
        转发消息

        Args:
            wxid (str): 消息接收人
            msgid (int): 消息id
        """

    def CGetQrcodeImage(self, wx_pid: int) -> bytes:
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

    def CGetA8Key(self, wx_pid: int, url: str) -> Tuple[JsonStr]:
        """
        获取A8Key

        Args:
            url (str): 公众号文章链接
        """

    def CSendXmlMsg(self, wx_pid: int, wxid: str, xml: str, img_path: str) -> int:
        """
        发送原始xml消息

        Returns:
            int: 0表示成功
        """

    def CLogout(self, wx_pid: int) -> int:
        """
        登出

        Returns:
            int: 0表示成功
        """

    def CGetTransfer(
        self, wx_pid: int, wxid: str, transactionid: str, transferid: int
    ) -> int:
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

    def CSendEmotion(self, wx_pid: int, wxid: str, img_path: str) -> int:
        ...

    def CGetMsgCDN(self, wx_pid: int, msgid: int) -> str:
        """
        下载图片、视频、文件等

        Returns:
            str
                成功返回文件路径，失败返回空字符串.
        """


class RobotEventSinkABC:
    def OnGetMessageEvent(self, msg):
        ...


class RobotEventABC:
    def CRegisterWxPidWithCookie(self, wx_pid: int, cookie: int):
        ...
