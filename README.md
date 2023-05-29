# WhoChat
```
 ___       __   ___  ___  ________  ________  ___  ___  ________  _________
|\  \     |\  \|\  \|\  \|\   __  \|\   ____\|\  \|\  \|\   __  \|\___   ___\
\ \  \    \ \  \ \  \\\  \ \  \|\  \ \  \___|\ \  \\\  \ \  \|\  \|___ \  \_|
 \ \  \  __\ \  \ \   __  \ \  \\\  \ \  \    \ \   __  \ \   __  \   \ \  \
  \ \  \|\__\_\  \ \  \ \  \ \  \\\  \ \  \____\ \  \ \  \ \  \ \  \   \ \  \
   \ \____________\ \__\ \__\ \_______\ \_______\ \__\ \__\ \__\ \__\   \ \__\
    \|____________|\|__|\|__|\|_______|\|_______|\|__|\|__|\|__|\|__|    \|__|
```

**一个依赖于 [ComWeChatRobot](https://github.com/ljc545w/ComWeChatRobot)提供的Com接口的微信机器人，在此之上提供了:**

1. 发布至PyPI，可以一键安装
2. 命令行支持，可以方便通过命令操作（见下面使用说明）
3. WebSocket消息推送
4. [JSON-RPC2.0](https://wiki.geekdream.com/Specification/json-rpc_2.0.html)方法调用，支持WebSocket和HTTP
5. 简单的定时任务支持
6. 其他

**当前支持微信版本为`3.7.0.30`, Python版本3.8及以上**

## 安装：
`pip install whochat`

若需要HTTP RPC支持，则是

`pip install whochat[httprpc]`

安装完成之后尝试使用`whochat`命令，理应看到以下输出：
```
D:\
> whochat --help
Usage: whochat [OPTIONS] COMMAND [ARGS]...

  微信机器人

  使用<子命令> --help查看使用说明

Options:
  --help  Show this message and exit.

Commands:
  list-wechat       列出当前运行的微信进程
  regserver         注册COM
  serve-message-ws  运行接收微信消息的Websocket服务
  serve-rpc-http    运行微信机器人RPC服务(JSON-RPC2.0), 使用HTTP接口
  serve-rpc-ws      运行微信机器人RPC服务(JSON-RPC2.0), 使用Websocket
  show-rpc-docs     列出RPC接口
  version           显示程序和支持微信的版本信息
```

## 使用
1. 列出当前运行的微信进程：
```
> whochat list-wechat
PID: 102852
启动时间: 2022-08-27T22:22:02.290700
运行状态: running
用户名: wxid_hjkafa123a
---
```

2. 注册COM服务：
```
> whochat regserver  # 注册
> whochat regserver --unreg  # 取消注册
```
注册一次就可以使用服务了。

3. 开启微信消息转发WebSocket服务
```
> whochat serve-message-ws --help
Usage: whochat serve-message-ws [OPTIONS] [WX_PIDS]...

  运行接收微信消息的Websocket服务

  WX_PIDS: 微信进程PID

Options:
  -h, --host TEXT     Server host.  [default: localhost]
  -p, --port INTEGER  Server port  [default: 9001]
  --help              Show this message and exit.
```
该子命令接受一或多个微信PID作为位置参数，可以指定地址
```
> whochat serve-message-ws 102852
注册SIGINT信号处理程序: WechatWebsocketServer.shutdown
开始运行微信消息接收服务
开始向客户端广播接收到的微信消息
开始运行微信Websocket服务，地址为：<localhost:9001>
{'wxId': 'wxid_hjkafa123a', 'wxNumber': 'wxid_hjkafa123a', 'wxNickName': 'Cider', 'Sex': '男', 'wxSignature': 'null', 'wxBigAvatar': 'http://wx.qlogo.cn/mmhead/ver_1/R50J6cxxTRzE28sY32DVJibeRUZPiaPotzPVjuReXZsONBdNZXQChSfrK0rDWh8RKS5ibt7VJdK0p22YJrOGjRA051lY9mwkt6ONruLmYTyBAA/0', 'wxSmallAvatar': 'http://wx.qlogo.cn/mmhead/ver_1/R50J6cxxTRzE28sY32DVJibeRUZPiaPotzPVjuReXZsONBdNZXQChSfrK0rDWh8RKS5ibt7VJdK0p22YJrOGjRA051lY9mwkt6ONruLmYTyBAA/132', 'wxNation': 'CN', 'wxProvince': 'Anhui', 'wxCity': 'Hefei', 'PhoneNumber': 'null'}
开启Robot消息推送
```
默认地址为`localhost:9001`，连接测试：
![WebSocket测试](https://user-images.githubusercontent.com/26922464/187036096-3a780aaa-e79e-4c82-abb2-9f7c402601a1.gif)

当前接收消息格式示例:
```json
{
    "extrainfo": {
        "is_at_msg": true,
        "at_user_list": [
            "wx_user_id1",
            "wx_user_id2"
        ],
        "member_count": 23
    },
    "filepath": "",
    "isSendMsg": 0,
    "message": "@wx_user1\u2005@wx_user2\u2005Hello",
    "msgid": 7495392442139043211,
    "pid": 17900,
    "sender": "20813132945@chatroom",
    "time": "2022-09-03 22: 10: 33",
    "type": 1,
    "wxid": "wx_user_id10"
}
```
4. 开启WebSocket RPC服务进行方法调用：
```
> whochat serve-rpc-ws
PID: 28824
注册SIGINT信号处理程序: run.<locals>.shutdown
运行微信机器人RPC websocket服务, 地址为<localhost:9002>
```
默认地址为`localhost:9002`，测试发送消息给文件传输助手，~~记得先调用`start_robot_service`注入dll~~，现在调用方法时会自动注入dll
![发送消息](https://user-images.githubusercontent.com/26922464/187036614-f1b8589b-ce2b-4c57-bbb0-c167755201a5.png)
RPC所有方法和参数可通过`whochat show-rpc-docs`命令查看或者`whochat show-rpc-docs --json > docs.json`生成JSON文档([rpc-api.json](docs/rpc/api.json)):
```
> whochat show-rpc-docs --help
Usage: whochat show-rpc-docs [OPTIONS]

  列出RPC接口

  whochat show-rpc-docs
  or
  whochat show-rpc-docs --json > docs.json

Options:
  --json  JSON文档
  --help  Show this message and exit.
```

5. 定时任务：

在每天上午6点整喊基友起床，同样使用RPC调用`schedule_a_job`（获取接口文档见*4*）,
```json
{
    "jsonrpc": "2.0",
    "method": "schedule_a_job",
    "params": {
        "name": "GETUP",
        "unit": "days",
        "every": 1,
        "at": "08:00:00",
        "do": {
            "func": "send_text",
            "args": [
                102852,
                "jiyou",
                "GET UP!"
            ]
        },
        "description": "",
        "tags": [
            "jiyou"
        ]
    },
    "id": 4
}
```

[CHANGELOG](https://github.com/amchii/whochat/blob/main/CHANGELOG.md)

[Tags](https://github.com/amchii/whochat/tags)
## v1.3.4
* 自动设置微信版本号避免更新
* 增加环境变量`WHOCHAT_WECHAT_VERSION`自定义微信版本号
* 尝试使`BotWebsocketRPCClient.rpc_call`更正确地运行

## v1.3.3
* 增加获取微信最新版本号的方法
* 修复Mac用户发送@消息无法正确解析的问题

## v1.3.2
* 修改日志级别，增加日志文件记录

## v1.3.0
* 增加RPC Websocket客户端
* 消息转发命令行增加`--welcome`参数决定是否在客户端连接是发送"hello"
* `hook_`方法返回路径
* 增加`prevent_revoke`阻止文件消息被撤回时被删除

## v1.2.1
* 更新适配 [Robot DLL](https://github.com/amchii/ComWeChatRobot/commit/f6d75778d22b590a4775e49b72cb9c19037d2671)
* 添加`_comtypes.py`方便在非Windows平台开发

## v.1.1.0

* 更新 [Robot DLL](https://github.com/ljc545w/ComWeChatRobot/commit/ff76f80ce2f3d979bf968d07f530701d834dc988)
* 接收消息增加`extrainfo`字段，当消息为群消息时可获取群成员数量和被@的人的微信ID
* 命令行增加`log-level`选项控制日志级别
* 调用bot方法时自动注入dll
* 添加 [docs/rpc/api.json](https://github.com/amchii/whochat/blob/main/docs/rpc/api.json)

## v1.0.1

* 添加Python版本依赖说明

## 欢迎学习交流，点个star⭐️
