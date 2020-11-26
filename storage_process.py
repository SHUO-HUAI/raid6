import argparse
import os
import random
import socket
import sys
from datetime import datetime
from config import Config
import struct
from communication import Communication


class Storage:
    def __init__(self, save_path, init=False):

        self.save_path = save_path

        if init:
            self.init()

    def init(self):
        for block in range(Config.BN):
            path = os.path.join(self.save_path, str(block) + '.bin')
            init_b = open(path, "wb")
            for _ in range(Config.BS):
                init_b.write(b'\x00')
            init_b.flush()
            init_b.close()

    def free_blocks(self):
        each_block_save_num = int(Config.BS // Config.BFI)
        b = range(Config.RBFM, Config.RBFM + Config.RBFS, 1)
        rbfs = [bid for bid in b]
        all_content = self.read(rbfs, record_file_info=True)

        if_occupy = []

        for block_i in range(Config.RBFM + Config.RBFS, Config.BN):
            content_id = block_i // each_block_save_num
            content_data_id = (block_i % each_block_save_num) * Config.BFI
            occupy = int(
                struct.unpack('I', all_content[content_id][content_data_id:content_data_id + Config.BFI])[0])
            if_occupy.append(occupy)
        no_occupy_index = [idx for idx in range(len(if_occupy)) if if_occupy[idx] == 0]
        return len(no_occupy_index)

    def write(self, contents, block_id=None, record_file_info=False):

        content_length = len(contents)
        assert content_length + Config.BFI <= Config.BS
        each_block_save_num = int(Config.BS // Config.BFI)

        if block_id is None:
            # random set block id
            b = range(Config.RBFM, Config.RBFM + Config.RBFS, 1)
            rbfs = [bid for bid in b]
            all_content = self.read(rbfs, record_file_info=True)

            if_occupy = []

            for block_i in range(Config.RBFM + Config.RBFS, Config.BN):
                content_id = block_i // each_block_save_num
                content_data_id = (block_i % each_block_save_num) * Config.BFI
                occupy = int(
                    struct.unpack('I', all_content[content_id][content_data_id:content_data_id + Config.BFI])[0])
                if_occupy.append(occupy)
            no_occupy_index = [idx for idx in range(len(if_occupy)) if if_occupy[idx] == 0]
            # print(no_occupy_index)
            block_id = random.sample(no_occupy_index, 1)[0]

        block_id = block_id + Config.RBFM + Config.RBFS

        # whether used for record file information
        if not record_file_info:
            assert block_id >= Config.RBFM + Config.RBFS
        else:
            assert block_id in range(Config.RBFM)

        # write contents to block id
        path = os.path.join(self.save_path, str(block_id) + '.bin')
        fr = open(path, "rb")
        data = fr.read()
        fw = open(path, "wb")
        fw.write(data)
        length = struct.pack('I', content_length)
        fw.seek(0x0)
        fw.write(length)
        fw.write(contents)
        fw.flush()
        fr.close()
        fw.close()

        if not record_file_info:
            content_id = block_id // each_block_save_num
            content_data_id = (block_id % each_block_save_num) * Config.BFI

            # record write block in RBFS
            path = os.path.join(self.save_path, str(Config.RBFM + content_id) + '.bin')
            fr = open(path, "rb")
            data = fr.read()
            fw = open(path, "wb")
            fw.write(data)
            record = struct.pack('I', 1)
            fw.seek(content_data_id)
            fw.write(record)
            fw.flush()
            fr.close()
            fw.close()

        return block_id

    def read(self, block_ids, record_file_info=False):

        if type(block_ids) == int:
            block_ids = [block_ids]

        all_content = []
        for block_id in block_ids:
            path = os.path.join(self.save_path, str(block_id) + '.bin')
            read_b = open(path, "rb")
            data = read_b.read()
            if not record_file_info:
                length = int(struct.unpack('I', data[:Config.BFI])[0])
                content = data[Config.BFI:length + Config.BFI]
                all_content.append(content)
            else:
                all_content.append(data)

        return all_content

    def delete(self, block_id):
        assert block_id >= Config.RBFM + Config.RBFS
        each_block_save_num = int(Config.BS // Config.BFI)
        content_id = block_id // each_block_save_num
        content_data_id = (block_id % each_block_save_num) * Config.BFI

        # record write block in RBFS
        path = os.path.join(self.save_path, str(Config.RBFM + content_id) + '.bin')
        fr = open(path, "rb")
        data = fr.read()
        fw = open(path, "wb")
        fw.write(data)
        record = struct.pack('I', 0)
        fw.seek(content_data_id)
        fw.write(record)
        fw.flush()
        fr.close()
        fw.close()

        return block_id

    def connect(self, host_ip, ports):
        com_ser = Communication(host_ip, ports, is_server=False, for_user=False)
        return com_ser


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Storage Process')
    parser.add_argument('--ip', default='127.0.0.1', type=str, help='main process ip address (default: localhost)')
    parser.add_argument('--storage_port', default=[9990 + port_i for port_i in range(Config.SN)], type=list,
                        help='main process ports for storage process')
    parser.add_argument('--path', default='', type=str, help='save path, blank for first run')
    args = parser.parse_args()

    init = False
    PATH = args.path
    if PATH == '':
        if not os.path.exists('./logs'):
            os.makedirs('./logs')
        PATH = datetime.now().strftime('%Y%m%d-%H-%M-%S-%f')[:-3]
        PATH = os.path.join('./logs', PATH)
        os.makedirs(PATH)
        init = True

    try:
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.connect(('8.8.8.8', 80))
        socketIpPort = skt.getsockname()
        my_ip = socketIpPort[0]
        skt.close()
    except socket.error as msg:
        print(msg)
        sys.exit(1)

    storage_process = Storage(PATH, init)
    com_service = storage_process.connect(my_ip, args.storage_port)  # my_ip is used for localhost test

    while True:
        command = com_service.receive()
        print(command)
        if command == Config.Read_storage:

            block_id = com_service.receive()
            contents = storage_process.read(block_id)  # return pure content
            com_service.send(contents)

        elif command == Config.Write_storage:

            contents = com_service.receive()
            block_id = com_service.receive()
            if block_id != 'None':
                success = storage_process.write(contents,block_id)
            else:
                success = storage_process.write(contents)
            com_service.send(success)

        elif command == 'delete':
            block_id = com_service.receive()
            success = storage_process.delete(block_id)
            com_service.send(success)
        elif command == Config.Free_blocks:
            free_blocks = storage_process.free_blocks()
            com_service.send(free_blocks)
        elif command == Config.Ping_storage:
            com_service.send(1)
        else:
            chaos = com_service.receive()
            com_service.send(Config.ERROR)
            raise Exception
