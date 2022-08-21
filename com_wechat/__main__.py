__all__ = ("main",)

import sys


def main():
    from com_wechat.cli import wechat_bot

    sys.exit(wechat_bot())
