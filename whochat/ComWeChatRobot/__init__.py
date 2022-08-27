import os.path

from whochat.utils import as_admin

CWeChatRobotEXE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "CWeChatRobot.exe")
)

__wechat_version__ = "3.7.0.30"


def register():
    as_admin(CWeChatRobotEXE_PATH, "/regserver")


def unregister():
    as_admin(CWeChatRobotEXE_PATH, "/unregserver")
