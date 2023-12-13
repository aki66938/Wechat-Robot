#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import requests
import openai


class ChatGPT:

    def __init__(self, conf: dict) -> None:
        openai.api_key = conf["key"]
        # 自己搭建或第三方代理的接口
        openai.api_base = conf["api"]
        proxy = conf["proxy"]
        if proxy:
            openai.proxy = {"http": proxy, "https": proxy}
        self.conversation_list = {}
        self.system_content_msg = {"role": "system", "content": conf["prompt"]}

    def __repr__(self):
        return 'ChatGPT'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            if conf.get("key") and conf.get("api") and conf.get("prompt"):
                return True
        return False
    
    

    def get_answer(self, question: str, wxid: str) -> str:
        # wxid或者roomid,个人时为微信id，群消息时为群id
        self.updateMessage(wxid, question, "user")

        try:
            ret = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k-0613",
                messages=self.conversation_list[wxid],
                temperature=0.2
            )

            rsp = ret["choices"][0]["message"]["content"]
            rsp = rsp[2:] if rsp.startswith("\n\n") else rsp
            rsp = rsp.replace("\n\n", "\n")
            self.updateMessage(wxid, rsp, "assistant")
        except openai.error.AuthenticationError as e3:
            rsp = "OpenAI API 认证失败，请检查 API 密钥是否正确"
        except openai.error.APIConnectionError as e2:
            rsp = "无法连接到 OpenAI API，请检查网络连接"
        except openai.error.APIError as e1:
            rsp = "OpenAI API 返回了错误：" + str(e1)
        except Exception as e0:
            rsp = "发生未知错误：" + str(e0)

        return rsp

    def updateMessage(self, wxid: str, question: str, role: str) -> None:
        now_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        time_mk = "当需要回答时间时请直接参考回复:"
        # 初始化聊天记录,组装系统信息
        if wxid not in self.conversation_list.keys():
            question_ = [
                self.system_content_msg,
                {"role": "system", "content": "" + time_mk + now_time}
            ]
            self.conversation_list[wxid] = question_

        # 当前问题
        content_question_ = {"role": role, "content": question}
        self.conversation_list[wxid].append(content_question_)

        for cont in self.conversation_list[wxid]:
            if cont["role"] != "system":
                continue
            if cont["content"].startswith(time_mk):
                cont["content"] = time_mk + now_time

        # 只存储10条记录，超过滚动清除
        i = len(self.conversation_list[wxid])
        if i > 10:
            print("滚动清除微信记录：" + wxid)
            # 删除多余的记录，倒着删，且跳过第一个的系统消息
            del self.conversation_list[wxid][1]

    def get_balance(self):
            queryUrl = 'https://api.openai.com/dashboard/billing/subscription'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Authorization': f'Bearer {openai.api_key}',
                'Accept': '*/*',
                'Host': 'api.openai.com',
                'Connection': 'keep-alive'
            }
            
            r = requests.get(queryUrl, headers=headers)
            if r:
                r="当前key的余额为：" + str(r.json()['soft_limit_usd'])+ "$"
                return r
            else:
                return "查不到！查不到！"


            # print("key:", get_usage("sk-xxx"))


if __name__ == "__main__":
    from configuration import Config
    config = Config().CHATGPT
    if not config:
        exit(0)

    chat = ChatGPT(config)

    while True:
        q = input(">>> ")
        try:
            time_start = datetime.now()  # 记录开始时间
            print(chat.get_answer(q, "wxid"))
            time_end = datetime.now()  # 记录结束时间

            print(f"{round((time_end - time_start).total_seconds(), 2)}s")  # 计算的时间差为程序的执行时间，单位为秒/s
        except Exception as e:
            print(e)
