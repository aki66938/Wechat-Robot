#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import socket

import requests
def get_public_ip():
    '''
    可获取本机的公网ip，需要设置路由器允许入站数据，并做好转发
    如果不行就用ddns的方法做好动态域名解析

    注意：如果路由器设置了代理，请配置好代理分流，不要代理本宿主机，会影响公网地址获取的准确性
    方式有两种：
    1、设置规则让运行机器人的电脑直连(弃用，音乐下载要访问youtube)
    2、设置api接口www.taobao.com直连，例如openwrt可以设置该域名以及域名对应的两个ip->61.174.43.210、61.174.43.211直连
    '''

    try:
        response = requests.get('http://www.taobao.com/help/getip.php')
        ip_match = re.search(r'ipCallback\(\{ip:"(\d+\.\d+\.\d+\.\d+)"\}\)', response.text)
        if ip_match:
            return ip_match.group(1)
        else:
            return "IP address not found"
    except requests.RequestException:
        return "Unable to determine public IP address"

def get_local_ip():
    '''
    获取本机局域网默认地址
    '''
    try:
        # 创建一个套接字并连接到外部服务器（通常不会实际连接，但可以获取本地IP）
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("223.5.5.5", 80))  # 使用 Google DNS 服务器来获取IP
        local_ip = sock.getsockname()[0]
        return local_ip
    except socket.error:
        return "Unable to determine local IP address"

#测试用
# local_ip = get_local_ip()
# print("My local IP address is:", local_ip)
# public_ip = get_public_ip()
# print("My public IP address is:", public_ip)
