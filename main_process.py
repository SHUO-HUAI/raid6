import argparse
import os
import random
import socket
import sys
from datetime import datetime
from config import Config
import struct
from communication import Communication


class Main:
    def __init__(self):
        self.a = 0

    def connect(self, ip, ports_for_storage, port_for_user):
        storage_com_ser = Communication(ip, ports_for_storage, is_server=True, for_user=False)
        user_com_ser = Communication(ip, port_for_user, is_server=True, for_user=True)
        return storage_com_ser, user_com_ser


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Storage Process')
    parser.add_argument('--storage_port', default=[9990 + port_i for port_i in range(Config.SN)], type=list,
                        help='ports for storage process')
    parser.add_argument('--user_port', default=12346, type=int, help='port for user process, only support one user')
    args = parser.parse_args()

    Main_process = Main()

    try:
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.connect(('8.8.8.8', 80))
        socketIpPort = skt.getsockname()
        my_ip = socketIpPort[0]
        skt.close()
    except socket.error as msg:
        print(msg)
        sys.exit(1)

    storage_com, user_com = Main_process.connect(my_ip, args.storage_port, args.user_port) # my_ip is used for localhost test
