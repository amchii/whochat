import sys

from whochat.utils import windows_only

if sys.platform == "win32":
    from comtypes import *  # noqa
    from comtypes import client  # noqa
else:

    COINIT_MULTITHREADED = 0x0
    COINIT_APARTMENTTHREADED = 0x2
    COINIT_DISABLE_OLE1DDE = 0x4
    COINIT_SPEED_OVER_MEMORY = 0x8

    class Unusable:
        def __call__(self, *args, **kwargs):
            windows_only()

    class UnusableModule:
        def __getattr__(self, item):
            return Unusable()

    CoInitialize = Unusable()
    CoUninitialize = Unusable()
    CoInitializeEx = Unusable()
    client = UnusableModule()
