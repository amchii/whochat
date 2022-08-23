__all__ = ("main",)

import sys


def main():
    from whochat.cli import wechat_bot

    sys.exit(wechat_bot())
