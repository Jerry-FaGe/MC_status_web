#!/usr/bin/python3
# -*-coding:utf-8-*-
"""
Created on 2020/11/24

@author: Jerry
"""
import re
import socket
import codecs
import dns.resolver
from urllib.parse import urlparse
from mcstatus import JavaServer


def parse_address(address):
    tmp = urlparse("//" + address)
    if not tmp.hostname:
        raise ValueError("Invalid address '%s'" % address)
    return tmp.hostname, tmp.port


class McStatus:
    def __init__(self, host, port=25565, timeout=0.6):
        self.host = host
        self.port = port
        self.timeout = timeout

    @staticmethod
    def lookup(address):
        host, port = parse_address(address)
        if port is None:
            port = 25565
            try:
                answers = dns.resolver.query("_minecraft._tcp." + host, "SRV")
                if len(answers):
                    answer = answers[0]
                    host = str(answer.target).rstrip(".")
                    port = int(answer.port)
            except Exception:
                pass

        return McStatus(host, port)

    @staticmethod
    def logger(server_info, server_host):
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write("=" * 32 + "\n")
            print("=" * 32)
            if server_info:
                f.write("***服务器已开启***\n")
                print("***服务器已开启***")
                f.write("\n")
                print("")
                f.write("服务器地址：%s\n" % server_host)
                print("服务器地址：%s" % server_host)
                f.write("服务器版本：%s (protocol %s)\n" % (server_info['version'], server_info['protocol']))
                print("服务器版本：%s (protocol %s)" % (server_info['version'], server_info['protocol']))
                f.write("服务器MOTD：%s\n" % server_info['MOTD'])
                print("服务器MOTD：%s" % server_info['MOTD'])
                f.write("服务器延迟：%s ms\n" % server_info['ping'])
                print("服务器延迟：%s ms" % server_info['ping'])
                f.write("在线玩家数：%s\n" % server_info['online_players'])
                print("在线玩家数：%s" % server_info['online_players'])
                f.write("最大玩家数：%s\n" % server_info['max_players'])
                print("最大玩家数：%s" % server_info['max_players'])
                f.write("玩家列表：%s\n" % server_info['players'])
                print("玩家列表：%s" % server_info['players'])
            else:
                f.write("*****服务器未开启*****\n")
                print("*****服务器未开启*****")
                f.write("\n")
                print("")
                f.write("服务器地址：%s\n" % server_host)
                print("服务器地址：%s" % server_host)
            print("=" * 32)

    def get_server_info(self):
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
            # print(server_info)
            return server_info, "%s:%s" % (self.host, self.port)
        except socket.error:
            return False, "%s:%s" % (self.host, self.port)

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
            self.logger(server_info, "%s:%s" % (self.host, self.port))
            return server_info, "%s:%s" % (self.host, self.port)
        except socket.error:
            self.logger(False, "%s:%s" % (self.host, self.port))
            return False, "%s:%s" % (self.host, self.port)
