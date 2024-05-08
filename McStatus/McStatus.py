#!/usr/bin/python3
# -*-coding:utf-8-*-
"""
Created on 2020/11/24

@author: Jerry_FaGe
"""
import re
import socket
import codecs
from urllib.parse import urlparse

import dns.resolver
from mcstatus import JavaServer


def parse_address(address):
    """
    解析地址
    """
    tmp = urlparse("//" + address)
    if not tmp.hostname:
        raise ValueError("Invalid address '%s'" % address)
    return tmp.hostname, tmp.port


def lookup(address):
    host, port = parse_address(address)
    if port:
        return host, port
    port = 25565
    try:
        answers = dns.resolver.query("_minecraft._tcp." + host, "SRV")
        if len(answers):
            answer = answers[0]
            host = str(answer.target).rstrip(".")
            port = int(answer.port)
    except Exception as e:
        print(f"[error] DNS query error: {e}")
    finally:
        return host, port


class McStatus:
    def __init__(self, address, timeout=0.6):
        self.host, self.port = lookup(address)
        self.timeout = timeout
    
    def _get_server_info_by_socket(self):
        """
        通过 socket 获取服务器信息
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip = socket.gethostbyname(self.host)
        try:
            s.settimeout(self.timeout)
            s.connect((ip, self.port))
            s.send(bytearray([0xFE, 0x01]))
            data_raw = s.recv(1024)
            s.close()

            # 两种解码方式(cp437)(utf-16)，切换释放注释并注释掉另一种

            # (cp437)
            # data = data_raw.decode('cp437').split('\x00\x00\x00')

            # (utf-16)这个可以看到MOTD和其他信息
            data = codecs.utf_16_be_decode(data_raw[1:])[0].split('\x00')
            data[3] = re.sub(r'§\w', "", data[3]).replace("  ", "").replace('\n', ",")

            server_info = {
                '0': data[0].replace("\x00", ""),
                '1': data[1].replace("\x00", ""),
                'version': data[2].replace("\x00", ""),
                'MOTD': data[3].replace("\x00", ""),
                'online_players': data[4].replace("\x00", ""),
                'max_players': data[5].replace("\x00", "")
            }
            return server_info
        except socket.error:
            return False

    def get_server_info(self):
        server_info = self._get_server_info_by_socket()
        return server_info, "%s:%s" % (self.host, self.port)

    def get_by_mcstatus(self):
        server = JavaServer(self.host, self.port)
        try:
            status = server.status()
            motd = status.description
            motd = re.sub(r'§\w', "", motd).replace("  ", "").replace('\n', ",")
            server_info = {
                'version': status.version.name,
                'MOTD': motd,
                'online_players': status.players.online,
                'max_players': status.players.max,
                'ping': status.latency,
                'protocol': status.version.protocol,
                'players': status.raw['players'].get('sample', None)
            }
            return server_info, "%s:%s" % (self.host, self.port)
        except socket.error:
            return False, "%s:%s" % (self.host, self.port)
