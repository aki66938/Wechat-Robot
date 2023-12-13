# -*- coding: utf-8 -*-

import logging
import re
import time


import requests


import xml.etree.ElementTree as ET
from queue import Empty
from threading import Thread
from music_http import HttpServer

from base.func_chatgpt import ChatGPT
from base.func_chengyu import cy
from base.func_news import News
from base.func_xinghuo_web import XinghuoWeb
from base.network_tools import location_send,domain_ip,ping_ip
from configuration import Config
from constants import ChatType
from job_mgmt import Job
from wcferry import Wcf, WxMsg

from base.api import get_kout_text

from base.session_manager import SessionManager
from music import Download, Search, dl_song


__version__ = "39.0.7.0"



import os


'''
全局化http实例，确保可以终止http服务
注：如果没有用指令终止http直接在终端ctrl+c，可能会卡线程导致端口被占，再次启动无法打开
解决办法：自己找线程杀死或者修改端口
'''
rpath = os.path.dirname(os.path.abspath(__file__))
mpath = os.path.join(rpath, 'music')
http_server = HttpServer(port=8000, directory=mpath) 
http_server_path =  ""
session_status = ""

class Robot(Job):
    
        def __init__(self, config: Config, wcf: Wcf, chat_type: int):
            self.wcf = wcf
            self.config = config
            self.LOG = logging.getLogger("Robot")
            self.wxid = self.wcf.get_self_wxid()
            self.allContacts = self.getAllContacts()
            # ... existing initialization code ...
            self.session_manager = SessionManager()
            
            if ChatType.is_in_chat_types(chat_type):
                if chat_type == ChatType.CHATGPT.value and ChatGPT.value_check(self.config.CHATGPT):
                    self.chat = ChatGPT(self.config.CHATGPT)
                elif chat_type == ChatType.XINGHUO_WEB.value and XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                    self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
                else:
                    self.LOG.warning("未配置模型")
                    self.chat = None
            else:
                if ChatGPT.value_check(self.config.CHATGPT):
                    self.chat = ChatGPT(self.config.CHATGPT)
                elif XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                    self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
                else:
                    self.LOG.warning("未配置模型")
                    self.chat = None

            self.LOG.info(f"已选择: {self.chat}")

        @staticmethod
        def value_check(args: dict) -> bool:
            if args:
                return all(value is not None for key, value in args.items() if key != 'proxy')
            return False

        def toAt(self, msg: WxMsg) -> bool:
            """处理被 @ 消息
            :param msg: 微信消息结构
            :return: 处理状态，`True` 成功，`False` 失败
            """
            return self.toChitchat(msg)
        
        def JuPai(self,msg: WxMsg) -> None:
            url = "https://v.api.aa1.cn/api/api-jupai/index.php?msg=" + (str(msg.content)).split("举牌=")[-1]
            self.LOG.error(url)
            if msg.from_group():
                self.wcf.send_image(url, msg.roomid)
            else:
                self.wcf.send_image(url, msg.sender)
        
        def handle_music_directive(self, msg: WxMsg)-> None:
                # 用户发送点歌命令时的处理逻辑
                global session_status
                        
                user_id = msg.sender + msg.roomid # 或者任何用于标识用户的唯一标识符
                session = self.session_manager.get_session(user_id)

                if "点歌=" in msg.content:
                    song_name = msg.content.split("点歌=")[1].strip()
                    self.LOG.error("点歌session_status = " + session_status)

                    session.store_data("song_name", song_name)
                    dl_song(user_id,http_server_path)
                    session.update_state("AWAITING_SONG_SELECTION")
                    session_status = session.state

                    # 将搜索结果发送回用户
                    song_list = session.retrieve_data("song_list") 
                    formatted_list = ""
                    for key, value in song_list.items():
                        formatted_list += f"{key}:{value}\n"
                    if msg.from_group():
                        self.sendTextMsg(formatted_list, msg.roomid)
                    else:
                        self.sendTextMsg(formatted_list, msg.sender)

                # 检查用户是否选择了1到20之间的歌曲索引
                elif any(str(i) in msg.content for i in range(1, 21)):
                    if session.state == "AWAITING_SONG_SELECTION":
                        self.LOG.error("选歌session_status = " + session_status)
                        
                        selected_index = msg.content  # 用户选择歌曲
                        session.store_data("selected_index", selected_index)
                        dl_song(user_id,http_server_path)
                        xml = session.retrieve_data("xml") 
                        img_url = session.retrieve_data("img_url") 
                        session.update_state("INITIAL")
                        if msg.from_group():
                            self.wcf.send_xml(msg.roomid,xml,3,img_url)
                        else:
                            self.wcf.send_xml(msg.sender,xml,3,img_url)
                else:
                    if session.state == "AWAITING_SONG_SELECTION":
                        content = "点完就跑？不愧是你"
                        session.update_state("INITIAL")
                        session_status = ""
                        if msg.from_group():
                            self.sendTextMsg(content, msg.roomid)
                        else:
                            self.sendTextMsg(content, msg.sender)
                    return
    
        def toChengyu(self, msg: WxMsg) -> bool:
            """
            处理成语查询/接龙消息
            :param msg: 微信消息结构
            :return: 处理状态，`True` 成功，`False` 失败
            """
            status = False
            texts = re.findall(r"^([#|?|？])(.*)$", msg.content)
            # [('#', '天天向上')]
            if texts:
                flag = texts[0][0]
                text = texts[0][1]
                if flag == "#":  # 接龙
                    if cy.isChengyu(text):
                        rsp = cy.getNext(text)
                        if rsp:
                            self.sendTextMsg(rsp, msg.roomid)
                            status = True
                elif flag in ["?", "？"]:  # 查词
                    if cy.isChengyu(text):
                        rsp = cy.getMeaning(text)
                        if rsp:
                            self.sendTextMsg(rsp, msg.roomid)
                            status = True

            return status
        

        def toChitchat(self, msg: WxMsg) -> bool:
            """闲聊，接入 ChatGPT
            """
            if not self.chat:  # 没接 ChatGPT，固定回复
                rsp = "你@我干嘛？"
            else:  # 接了 ChatGPT，智能回复
                q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
                rsp = self.chat.get_answer(q, (msg.roomid if msg.from_group() else msg.sender))

            if rsp:
                if msg.from_group():
                    self.sendTextMsg(rsp, msg.roomid)
                else:
                    self.sendTextMsg(rsp, msg.sender)

                return True
            else:
                self.LOG.error(f"无法从 ChatGPT 获得答案")
                return False

        def handle_message(self, msg: WxMsg):
            '''
            开启用于音乐播放的http接口，本地环境可以访问-->http://localhost:8000
            要用于发送xml则将8000端口并且最外层的路由器吧端口通过ipv6暴露出去
            ipv4需开启ddos
            还不知道什么是ddos？
            这里有个例子-->https://www.ioiox.com/archives/112.html
            '''
            if msg.content == "开启music_http":
                global http_server_path 
                http_server_path= http_server.start()
                content = f"来活了来活了ᕕ( ᐛ )ᕗ，快看这里-->" + http_server_path
                self.sendTextMsg(content,msg.sender)
                return True
            elif msg.content == "关闭music_http":
                content = http_server.stop()
                self.sendTextMsg(content,msg.sender)
                return False
            else:
                return
        
        def key_balance(self,msg: WxMsg) -> None:
            balance = self.chat.get_balance()
            if msg.from_group():
                self.sendTextMsg(balance, msg.roomid)
            else:
                self.sendTextMsg(balance, msg.sender)

        def rich_text(self):
            '''
            卡片样式：
                |-------------------------------------|
                |title, 最长两行
                |(长标题, 标题短的话这行没有)
                |digest, 最多三行，会占位    |--------|
                |digest, 最多三行，会占位    |thumburl|
                |digest, 最多三行，会占位    |--------|
                |(account logo) name
                |-------------------------------------|
            Args:
                name (str): 左下显示的名字
                account (str): 填公众号 id 可以显示对应的头像（gh_ 开头的）
                title (str): 标题，最多两行
                digest (str): 摘要，三行
                url (str): 点击后跳转的链接
                thumburl (str): 缩略图的链接
                receiver (str): 接收人, wxid 或者 roomid
            '''
            name = '管理员'
            account = ''
            title = '测试公告'
            digest = '''测试+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            '''
            url = 'https://github.com/lich0821/WeChatFerry'
            thumburl = 'https://tv.yyfoam.top/emby/Items/428553/Images/Primary?maxHeight=375&maxWidth=375&tag=7b174831d5075aaf3d61c753eca68b8a&keepAnimation=true&quality=90'
            receiver = 'wxid_2hlw5d0mkho441'
            self.wcf.send_rich_text(name,account,title,digest,url,thumburl,receiver)


        def processMsg(self, msg: WxMsg) -> None:
            """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
            此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
            群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
            content = "xx天气信息为："
            receivers = msg.roomid
            self.sendTextMsg(content, receivers, msg.sender)
            """
            global session_status
            INAPPROPRIATE_WORDS = ["狗日的", "你出去", "你滚"]
            WARNING_MESSAGE = "因言论不当@{} ，已被移出群聊。欢迎下次注意言辞再加入。"

            # 群聊消息
            if msg.from_group():
                if any(re.search(word, msg.content) for word in INAPPROPRIATE_WORDS):
                    # 使用 groupdel 配置进行检查
                    if msg.roomid in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                        self.wcf.del_chatroom_members(msg.roomid, msg.sender)  # 踢出操作
                        alias = self.wcf.get_alias_in_chatroom(msg.sender, msg.roomid)
                        warning_message = WARNING_MESSAGE.format(alias)
                        self.sendTextMsg(warning_message, msg.roomid)  # 发送警告信息
                        return

                elif msg.is_at(self.wxid):  # 被@
                    self.toAt(msg)
   
                else:  # 其他消息
                    if "查ip=" in msg.content:
                        location_send(self,msg)
                    elif "#余额" in msg.content:
                        self.key_balance(msg)
                    elif "给我骂他↑" in msg.content:
                        get_kout_text(self,msg)
                    elif "ping=" in msg.content:
                        ping_ip(self,msg)
                    elif "举牌=" in msg.content:
                        self.JuPai(msg)
                    elif "域名=" in msg.content:
                        domain_ip(self,msg)
                    elif "点歌=" in msg.content:
                        self.handle_music_directive(msg)
                    elif session_status != "":
                        self.LOG.error("聊天session_status = " + session_status)
                        self.handle_music_directive(msg)
                    else:
                        self.toChengyu(msg)

                return  # 处理完群聊信息，后面就不需要处理了

            # 非群聊信息，按消息类型进行处理
            if msg.type == 37:  # 好友请求
                self.autoAcceptFriendRequest(msg)

            elif msg.type == 10000:  # 系统信息
                self.sayHiToNewFriend(msg)

            elif msg.type == 0x01:  # 文本消息
                # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
                if msg.from_self():
                    if msg.content == "^更新$":
                        self.config.reload()
                        self.LOG.info("已更新")
                elif "入群" in msg.content:
                    self.LOG.error(msg.content)
                    roomid = '39182538551@chatroom'
                    self.wcf.invite_chatroom_members(msg.sender,roomid)
                    self.LOG.error(self.wcf.invite_chatroom_members(msg.sender,roomid))
                elif "查ip=" in msg.content:
                    location_send(self,msg)
                elif "#余额" in msg.content:
                    self.key_balance(msg)
                elif "ping=" in msg.content:
                    ping_ip(self,msg)
                elif "举牌=" in msg.content:
                    self.JuPai(msg)
                elif "发公告" in msg.content:
                    self.rich_text()
                elif "域名=" in msg.content:
                    domain_ip(self,msg)
                elif "开启music_http" in msg.content or "关闭music_http" in msg.content:
                    self.handle_message(msg)
                elif "点歌=" in msg.content:
                    self.handle_music_directive(msg)
                elif session_status != "":
                    self.handle_music_directive(msg)
                else:
                    self.toChitchat(msg)  # 闲聊

        def onMsg(self, msg: WxMsg) -> int:
            try:
                self.LOG.info(msg)  # 打印信息
                self.processMsg(msg)
            except Exception as e:
                self.LOG.error(e)

            return 0

        def enableRecvMsg(self) -> None:
            self.wcf.enable_recv_msg(self.onMsg)

        def enableReceivingMsg(self) -> None:
            def innerProcessMsg(wcf: Wcf):
                while wcf.is_receiving_msg():
                    try:
                        msg = wcf.get_msg()
                        self.LOG.info(msg)
                        self.processMsg(msg)
                    except Empty:
                        continue  # Empty message
                    except Exception as e:
                        self.LOG.error(f"Receiving message error: {e}")

            self.wcf.enable_receiving_msg()
            Thread(target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True).start()

        def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
            """ 发送消息
            :param msg: 消息字符串
            :param receiver: 接收人wxid或者群id
            :param at_list: 要@的wxid, @所有人的wxid为：notify@all
            """
            # msg 中需要有 @ 名单中一样数量的 @
            ats = ""
            if at_list:
                if at_list == "notify@all":  # @所有人
                    ats = " @所有人"
                else:
                    wxids = at_list.split(",")
                    for wxid in wxids:
                        # 根据 wxid 查找群昵称
                        ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

            # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
            if ats == "":
                self.LOG.info(f"To {receiver}: {msg}")
                self.wcf.send_text(f"{msg}", receiver, at_list)
            else:
                self.LOG.info(f"To {receiver}: {ats}\r{msg}")
                self.wcf.send_text(f"{ats}\n\n{msg}", receiver, at_list)

        def getAllContacts(self) -> dict:
            """
            获取联系人（包括好友、公众号、服务号、群成员……）
            格式: {"wxid": "NickName"}
            """
            contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
            return {contact["UserName"]: contact["NickName"] for contact in contacts}

        def keepRunningAndBlockProcess(self) -> None:
            """
            保持机器人运行，不让进程退出
            """
            while True:
                self.runPendingJobs()
                time.sleep(1)

        def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
            try:
                xml = ET.fromstring(msg.content)
                v3 = xml.attrib["encryptusername"]
                v4 = xml.attrib["ticket"]
                scene = int(xml.attrib["scene"])
                self.wcf.accept_new_friend(v3, v4, scene)

            except Exception as e:
                self.LOG.error(f"同意好友出错：{e}")

        def sayHiToNewFriend(self, msg: WxMsg) -> None:
            nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
            if nickName:
                # 添加了好友，更新好友列表
                self.allContacts[msg.sender] = nickName[0]
                self.sendTextMsg(f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender)

        def newsReport(self) -> None:
            receivers = self.config.NEWS
            if not receivers:
                return

            news = News().get_important_news()
            for r in receivers:
                self.sendTextMsg(news, r)