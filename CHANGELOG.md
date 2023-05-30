# Changelog
```
 ___       __   ___  ___  ________  ________  ___  ___  ________  _________
|\  \     |\  \|\  \|\  \|\   __  \|\   ____\|\  \|\  \|\   __  \|\___   ___\
\ \  \    \ \  \ \  \\\  \ \  \|\  \ \  \___|\ \  \\\  \ \  \|\  \|___ \  \_|
 \ \  \  __\ \  \ \   __  \ \  \\\  \ \  \    \ \   __  \ \   __  \   \ \  \
  \ \  \|\__\_\  \ \  \ \  \ \  \\\  \ \  \____\ \  \ \  \ \  \ \  \   \ \  \
   \ \____________\ \__\ \__\ \_______\ \_______\ \__\ \__\ \__\ \__\   \ \__\
    \|____________|\|__|\|__|\|_______|\|_______|\|__|\|__|\|__|\|__|    \|__|
```

[Tags](https://github.com/amchii/whochat/tags)
## v1.3.5
* 解析最新微信版本`extra_info`
* Log raw message at debug level

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

## v1.1.0

* 更新 [Robot DLL](https://github.com/ljc545w/ComWeChatRobot/commit/ff76f80ce2f3d979bf968d07f530701d834dc988)
* 接收消息增加`extrainfo`字段，当消息为群消息时可获取群成员数量和被@的人的微信ID
* 命令行增加`log-level`选项控制日志级别
* 调用bot方法时自动注入dll
* 添加 [docs/rpc/api.json](docs/rpc/api.json)

## v1.0.1

* 添加Python版本依赖说明
