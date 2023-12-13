# Wechat-Robot
一个玩微信的机器人
基于wcferry的robot demo魔改，增加了一些运维实用功能
感谢大佬lich0821开源的wcferry及其机器人项目

## 目前功能
- AI助手
- 当前gpt-key密钥查询
- 查ip归属地
- ip测速
- 查域名ip（类似nslookup）
- 全网点歌台（暂未实现xml发送）

## 点歌台功能说明

由于音乐分享需要公网可访问实际资源，因此该方式采用本地存储音乐文件的方式分享音乐，使得机器人可以部署在本地环境。

实现方式基于session_manager.py模块和music_http.py模块。
暂未考虑实用数据库管理用户状态，
其中session模块用户管理用户状态，http则则是由my_ip.py模块搭配获取本地公网ip后，临时开启http服务使得用户发送的xml卡片可以访问本地实际的音乐文件。

通过个人微信控制机器人微信的http服务的开关。如果不开启http功能则无法分享音乐卡片

![IMG_202312129983_196x50](https://github.com/aki66938/Wechat-Robot/assets/47413858/d3022472-aaf9-4d94-9bbf-40ae9d320ba9)
