import random
import re
import socket
import string
import typing


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
def guess_wechat_user_by_path(path: str) -> typing.Optional[str]:
    """

    :param path: e.g. "C:\\Users\\foo\\Documents\\WeChat Files\\<wxid>\\Msg\\Sns.db"
    """

    m = re.match(r".*?WeChat Files\\([\w\-]+)\\", path, flags=re.I)
    if not m:
        return ""
    return m.group(1)
