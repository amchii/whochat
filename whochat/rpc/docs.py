import inspect
from collections import OrderedDict

from whochat.rpc.handlers import make_rpc_methods

_docs = []


def make_docs():
    if _docs:
        return _docs
    rpc_methods = make_rpc_methods()

    for name, rpc_method in OrderedDict(
        {key: rpc_methods[key] for key in sorted(rpc_methods.keys())}
    ).items():
        s = inspect.signature(rpc_method)
        description = rpc_method.__doc__
        params = []
        if rpc_method.__qualname__.split(".", maxsplit=1)[0] == "WechatBot":
            params.append(
                {
                    "name": "wx_pid",
                    "default": None,
                    "required": True,
                }
            )
        for param in s.parameters.values():
            if param.name == "self":
                continue
            params.append(
                {
                    "name": param.name,
                    "default": None if param.default is param.empty else param.default,
                    "required": param.default is param.empty,
                }
            )
        _docs.append({"name": name, "description": description, "params": params})

    return _docs


def pretty_docs():
    docs = make_docs()
    s = ""
    for item in docs:
        s += f"Name: `{item['name']}`\n"
        s += f"Description: \n\t{item['description'].lstrip() if item['description'] else '无'}\n"
        s += "Params: \n\t"
        for param in item["params"]:
            s += f"Name: `{param['name']}`\n\t"
            s += f"Required: `{str(param['required']).lower()}`\n\t"
            s += (
                f"Default: `{param['default']}`\n"
                if param["default"] is not None
                else "\n\t"
            )

        s += "\n-----------------------------------------------------\n"
    return s
