import re
import json
import subprocess
import urllib.parse
import ipaddress
import requests
import dns.resolver
from wcferry import WxMsg

def is_valid_ipv4(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def ip_location(ip: str) -> str:
    url = 'https://restapi.amap.com/v3/ip'
    params = {
        'key': '0113a13c88697dcea6a445584d535837',
        'ip': ip
    }
    full_url = f'{url}?{urllib.parse.urlencode(params)}'
    response = urllib.request.urlopen(full_url)
    data = json.loads(response.read().decode('utf-8'))

    city = data.get('city', '')
    if isinstance(city, list):
        city = ''

    province = data.get('province', '')
    if isinstance(province, list):
        province = ''

    location = province + city

    return f"{ip}查询结果为：{location}"

def location_send(self, msg: WxMsg) -> None:
    content = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', msg.content)
    if is_valid_ipv4(content[0]):
        if msg.from_group():
            self.sendTextMsg(ip_location(content[0]), msg.roomid)
        else:
            self.sendTextMsg(ip_location(content[0]), msg.sender)
    else:
        content = "臭傻逼，是不是ip你自己不会看吗？"
        if msg.from_group():
            self.sendTextMsg(content, msg.roomid)
        else:
            self.sendTextMsg(content, msg.sender)

def domain_ip(self, msg: WxMsg) -> list:
    domain = msg.content.replace("域名=", "")
    ips = []
    try:
        answers = dns.resolver.resolve(domain, 'A')  # 'A' record for IPv4 addresses
        for rdata in answers:
            ips.append(rdata.to_text())
    except Exception as e:
        print(f"Error occurred: {e}")
    ip_str = "域名下有这么些个ip:\n"
    if ips:
        ip_str += '\n'.join(ips)
        if msg.from_group():
            self.sendTextMsg(ip_str, msg.roomid)
        else:
            self.sendTextMsg(ip_str, msg.sender)
    else:
        content = "你知道它不是域名还丢给我看?"
        if msg.from_group():
            self.sendTextMsg(content, msg.roomid)
        else:
            self.sendTextMsg(content, msg.sender)
    return ips

def ping_ip(self, msg: WxMsg) -> None:
    content = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', msg.content)
    try:
        if is_valid_ipv4(content[0]):
            output = subprocess.check_output(['ping', content[0]])
            if msg.from_group():
                self.sendTextMsg(output.decode('gbk'), msg.roomid)
            else:
                self.sendTextMsg(output.decode('gbk'), msg.sender)
        else:
            content = "臭傻逼，是不是ip你自己不会看吗？"
            if msg.from_group():
                self.sendTextMsg(content, msg.roomid)
            else:
                self.sendTextMsg(content, msg.sender)
    except subprocess.CalledProcessError as e:
        content = "糟糕，机器人网络出了点问题:" + str(e)
        if msg.from_group():
            self.sendTextMsg(content, msg.roomid)
        else:
            self.sendTextMsg(content, msg.sender)

