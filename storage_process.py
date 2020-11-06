import argparse
import os
from datetime import datetime
from config import Config
import struct


def read_block(PATH):
    return -1


def write_block(PATH1, PATH2):
    i = 0
    with open(PATH2, 'rb+') as read_b:
        p = os.path.join(PATH1,i)
        while True:
            content1 = read_b.read(32*1024)
            with open(p,'wb+') as w_b:

            print(len(content1))
            if len(content1) == 0:
                break
            else:
                print(content1)

    # contents.
    # print(contents)
    # print(contents[0])


class Storage:
    def __init__(self, block_size, block_num, save_path, reverse_block1, reverse_block2, init=False):
        self.block_size = block_size
        self.block_num = block_num
        self.save_path = save_path
        self.reverse_block1 = reverse_block1
        self.reverse_block2 = reverse_block2
        if init:
            self.init()

    def init(self):
        return -1

    def write(self, contents):
        return -1

    def read(self, block_id):
        return -1

    def delete(self, block_id):
        return -1

    def connect(self, host_ip, port):
        return -1


if __name__ == '__main__':
    write_block(',', './imgs/aa.png')
    # parser = argparse.ArgumentParser(description='Storage Process')
    # parser.add_argument('--ip', default='127.0.0.1', type=str, help='main process ip address (default: localhost)')
    # parser.add_argument('--port', default=12345, type=int, help='main process port for storage (default 12345)')
    # parser.add_argument('--path', default='', type=str, help='save path, blank for first run')
    # args = parser.parse_args()
    #
    # config = Config()
    #
    # init = False
    # PATH = args.path
    # if PATH == '':
    #     if not os.path.exists('./logs'):
    #         os.makedirs('./logs')
    #     PATH = datetime.now().strftime('%Y%m%d-%H-%M-%S-%f')[:-3]
    #     PATH = os.path.join('./logs', PATH)
    #     init = True
    #
    # storage_process = Storage(config.BS, config.BN, PATH, config.RBFM, config.RBFS, init)
    # com_service = storage_process.connect(args.ip, args.port)
    #
    # while True:
    #     command = com_service.receive()
    #     if command == 'read':
    #
    #         block_id = com_service.receive()
    #         contents = storage_process.read(block_id)
    #         com_service.send(contents)
    #
    #     elif command == 'write':
    #
    #         contents = com_service.receive()
    #         success = storage_process.write(contents)
    #         com_service.send(success)
    #
    #     elif command == 'delete':
    #         block_id = com_service.receive()
    #         success = storage_process.delete(block_id)
    #         com_service.send(success)
    #     else:
    #         chaos = com_service.receive()
    #         com_service.send(-1)
    #         raise Exception
