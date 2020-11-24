import argparse
import os
import random
import socket
import sys
from datetime import datetime
from config import Config
import struct
from communication import Communication


class User:
    def __init__(self):
        self.a = 0

    def connect(self, host_ip, port):
        com_ser = Communication(host_ip, port, is_server=False, for_user=True)
        return com_ser


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='User Process')
    parser.add_argument('--ip', default='127.0.0.1', type=str, help='main process ip address (default: localhost)')
    parser.add_argument('--user_port', default=12346, type=int, help='main process ports for user process')
    args = parser.parse_args()
