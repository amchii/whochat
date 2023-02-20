import ctypes
import random
import re
import socket
import string
import sys
from typing import List, Optional


def windows_only():
    if sys.platform != "win32":
        raise RuntimeError("仅支持在win32环境下使用")


def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    ip, port = s.getsockname()
    s.close()
    return port


def get_random_string(size):
    sample = string.ascii_letters + string.digits
    if size <= len(sample):
        return "".join(random.sample(sample, k=size))
    return get_random_string(len(sample)) + get_random_string(size - len(sample))


# Windows Only
def guess_wechat_user_by_path(path: str) -> Optional[str]:
    """

    :param path: e.g. "C:\\Users\\foo\\Documents\\WeChat Files\\<wxid>\\Msg\\Sns.db"
    """

    m = re.match(r".*?WeChat Files\\([\w\-]+)\\", path, flags=re.I)
    if not m:
        return ""
    return m.group(1)


def guess_wechat_user_by_paths(paths: List[str]) -> Optional[str]:
    for path in paths:
        user = guess_wechat_user_by_path(path)
        if user:
            return user
    return ""


def guess_wechat_base_directory_by_path(path: str) -> Optional[str]:
    """
    :param path: e.g. "C:\\Users\\foo\\Documents\\WeChat Files\\<wxid>\\Msg\\Sns.db"
    """
    m = re.match(r"(.*?\\WeChat Files).*", path, flags=re.I)
    if not m:
        return ""
    return m.group(1)


def guess_wechat_base_directory(paths: List[str]) -> Optional[str]:
    for path in paths:
        directory = guess_wechat_base_directory_by_path(path)
        if directory:
            return directory
    return ""


_handles_type = ctypes.c_void_p * 1
RPC_S_CALLPENDING = -2147417835


class EventWaiter:
    def __init__(self, timeout: int):
        self.timeout = timeout
        self.handle = None
        self._handles = None

    def reset_event(self):
        return ctypes.windll.kernel32.ResetEvent(self.handle)

    def set_event(self):
        return ctypes.windll.kernel32.SetEvent(self.handle)

    def create_handle(self):
        self.handle = ctypes.windll.kernel32.CreateEventA(None, True, False, None)
        self._handles = _handles_type(self.handle)

    def close_handle(self):
        return ctypes.windll.kernel32.CloseHandle(self.handle)

    def stop(self):
        return self.set_event() != 0

    def wait_once(self) -> bool:
        try:
            res = ctypes.oledll.ole32.CoWaitForMultipleHandles(
                0,
                int(self.timeout * 1000),
                len(self._handles),
                self._handles,
                ctypes.byref(ctypes.c_ulong()),
            )
            return res == 0
        except WindowsError as details:
            if details.winerror == RPC_S_CALLPENDING:  # timeout expired
                return False
            raise

    def wait_forever(self):
        self.reset_event()
        try:
            while not self.wait_once():
                pass
        finally:
            self.close_handle()


def as_admin(exe: str, params: str = None):
    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params)
