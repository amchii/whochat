__all__ = ("main",)

import sys


def main():
    from whochat.cli import whochat

    sys.exit(whochat())
