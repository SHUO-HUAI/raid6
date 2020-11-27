import argparse
import os
import random
import socket
import sys
from datetime import datetime
from config import Config
import struct
import numpy as np
from communication import Communication
import check_error

class Main:
    def __init__(self, ip, ports_for_storage, port_for_user):

        storage_com_ser = Communication(ip, ports_for_storage, is_server=True, for_user=False)
        user_com_ser = Communication(ip, port_for_user, is_server=True, for_user=True)
        self.check_error = check_error.Verifier()
        # user_com_ser = None
        self.storage_ser = storage_com_ser
        self.user_com = user_com_ser
        self.ports_for_storage = ports_for_storage

        self.write_finish = False  # used for record a file if finishing writing
        self.write_record_tmp = []  # used for tmp save write information
        self.all_record_files = {}  # record all save files, including the filename and storage location, save down
        # when shutdown

    def write(self, content, filename=None):
        # need to determine which storage save this content
        # every time write a block to a storage for balance
        # the last time for writing a file will record its information
        # need to be done: p q
        self.ping()
        assert not self.write_finish or filename is not None

        if not self.write_finish:
            free_blocks_each_stroage = []
            for s_id in range(Config.SS):
                self.storage_ser.send(Config.Free_blocks, s_id)
                free_blocks = self.storage_ser.receive(s_id)
                free_blocks_each_stroage.append(len(free_blocks))
            free_blocks_each_stroage = np.array(free_blocks_each_stroage)

            # print(free_blocks_each_stroage)
            storage_id = free_blocks_each_stroage.argmax()  # save content to the most empty storage
            # print(storage_id)

            self.storage_ser.send(Config.Write_storage, storage_id)  # write commend
            self.storage_ser.send('None', storage_id)  # block id
            self.storage_ser.send(content, storage_id)  # content
            block_id = self.storage_ser.receive(storage_id)
            assert block_id != Config.ERROR
            self.write_record_tmp.append((storage_id, block_id))

            # for computing p q
            all_contents_for_pq = []
            for s_id in range(Config.SS):
                self.storage_ser.send(Config.Read_storage_For_p, s_id)  # read commend
                self.storage_ser.send(block_id, s_id)  # read block
                content_read = self.storage_ser.receive(s_id)
                all_contents_for_pq.append(content_read)
            p_block, q_block = self.check_error.parties_renew(all_contents_for_pq)
            # print('p_block', len(p_block))
            # print('q_block', len(q_block))

            # for writing p q
            self.storage_ser.send(Config.Write_storage_For_p, Config.SS)  # write commend for p
            self.storage_ser.send(block_id, Config.SS)  # write block id
            self.storage_ser.send(p_block, Config.SS)
            self.storage_ser.receive(Config.SS)

            self.storage_ser.send(Config.Write_storage_For_p, Config.SS + 1)  # write commend for p
            self.storage_ser.send(block_id, Config.SS + 1)  # write block id
            self.storage_ser.send(q_block, Config.SS + 1)
            self.storage_ser.receive(Config.SS + 1)

        else:
            assert filename not in self.all_record_files.keys()
            self.all_record_files[filename] = np.array(self.write_record_tmp)
            self.write_record_tmp = []
            self.write_finish = False
        print('Write done')

    def read(self, filename):
        self.ping()
        assert filename in self.all_record_files.keys()
        write_records = self.all_record_files[filename]
        all_content = b''
        for record in write_records:
            storage_id = record[0]
            block_id = record[1]

            self.storage_ser.send(Config.Read_storage, storage_id)
            self.storage_ser.send(block_id, storage_id)
            content = self.storage_ser.receive(storage_id)

            # length = int(struct.unpack('I', content_i[0][:Config.BFI])[0])
            # content = content_i[0][Config.BFI:length + Config.BFI]

            all_content = all_content + content[0]
        print('Read done')
        return all_content

    def delete(self, filename):
        # no need to modify the content in original storage block
        # because in read, that block still can be read out for verifying, its length is not zero
        # in write, this block will be used again and p q value will be updated automatically
        self.ping()
        assert filename in self.all_record_files.keys()
        write_records = self.all_record_files[filename]
        for record in write_records:
            storage_id = record[0]
            block_id = record[1]

            self.storage_ser.send(Config.Delete_block, storage_id)
            self.storage_ser.send(block_id, storage_id)
            SUCC = self.storage_ser.receive(storage_id)
            assert SUCC != Config.ERROR
        self.all_record_files.pop(filename)
        print('Delete done')

    def modify(self, content, filename):
        # delete and write, as write commend need to be called more than one times. so this method will implement
        # in main function
        pass

    def ping(self):
        # ping is used to guarantee all storage is connected
        broken_ids = []
        for s_id in range(Config.SN):
            SUCC = self.storage_ser.send(Config.Ping_storage, s_id)
            if SUCC == Config.SUCC:
                self.storage_ser.receive(s_id)
                print(str(s_id) + ' is alive')
            else:
                print(str(s_id) + ' is shutdown')
                broken_ids.append(s_id)

        if len(broken_ids) > 0:
            print('Begin Recovering')
            all_contents_for_recovery = {}
            for s_id in range(Config.SN):
                if s_id not in broken_ids:
                    for block_i in range(Config.BN):
                        self.storage_ser.send(Config.Read_storage_For_p, s_id)
                        self.storage_ser.send(block_i, s_id)
                        content = self.storage_ser.receive(s_id)
                        all_contents_for_recovery[(s_id, block_i)] = content

            all_recover_data = self.check_error.recover(broken_ids, all_contents_for_recovery)
            self.storage_ser.hock_for_broken(broken_ids)

            for key in all_recover_data.keys():
                storage_id = key[0]
                block_id = key[1]
                if storage_id in broken_ids and block_id not in range(Config.RBFM, Config.RBFM + Config.RBFS):
                    self.storage_ser.send(Config.Write_storage_For_p, storage_id)
                    self.storage_ser.send(block_id, storage_id)
                    self.storage_ser.send(all_recover_data[(storage_id, block_id)][0], storage_id)
                    block_id = self.storage_ser.receive(storage_id)
                    # print(block_id)
            print('Recovering done')
        print('Ping Done')

    def check_corruption(self, block_id):

        all_contents_for_pq = []
        for s_id in range(Config.SS):
            self.storage_ser.send(Config.Read_storage_For_p, s_id)  # read commend
            self.storage_ser.send(block_id, s_id)  # read block
            content_read = self.storage_ser.receive(s_id)
            all_contents_for_pq.append(content_read)
        p_block, q_block = self.check_error.parties_renew(all_contents_for_pq)

        self.storage_ser.send(Config.Read_storage_For_p, Config.SS)
        self.storage_ser.send(block_id, Config.SS)
        p_read = self.storage_ser.receive(Config.SS)

        self.storage_ser.send(Config.Read_storage_For_p, Config.SS + 1)
        self.storage_ser.send(block_id, Config.SS + 1)
        q_read = self.storage_ser.receive(Config.SS + 1)

        if p_block == p_read and q_block == q_read:
            return Config.SUCC
        else:
            return Config.ERROR


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Main Process')
    parser.add_argument('--storage_port', default=[9990 + port_i for port_i in range(Config.SN)], type=list,
                        help='ports for storage process')
    parser.add_argument('--user_port', default=12346, type=int, help='port for user process, only support one user')
    args = parser.parse_args()

    try:
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.connect(('8.8.8.8', 80))
        socketIpPort = skt.getsockname()
        my_ip = socketIpPort[0]
        skt.close()
    except socket.error as msg:
        print(msg)
        sys.exit(1)

    # my_ip is used for localhost test
    # it will first wait all storage processes to connect
    # then it will wait user process to connect, then it will listen to user's command
    # storage_com, user_com = Main_process.connect(my_ip, args.storage_port, args.user_port)
    Main_process = Main(my_ip, args.storage_port, args.user_port)
    while True:
        try:
            command = Main_process.user_com.receive()
            filename = Main_process.user_com.receive()
            if command == Config.Write_For_User:
                contents = Main_process.user_com.receive()
                Main_process.write_finish = False

                for content1 in contents:
                    Main_process.write(content1)

                Main_process.write_finish = True
                Main_process.write(0, filename)
                Main_process.user_com.send(Config.SUCC)

            elif command == Config.Read_For_User:
                content = Main_process.read(filename)
                Main_process.user_com.send(content)

            elif command == Config.Delete_For_User:
                Main_process.delete(filename)

            elif command == Config.Modify_For_User:
                Main_process.delete(filename)

                contents = Main_process.user_com.receive()
                Main_process.write_finish = False

                for content1 in contents:
                    Main_process.write(content1)

                Main_process.write_finish = True
                Main_process.write(0, filename)

            else:
                chaos = Main_process.user_com.receive()
                raise Exception
        except Exception as e:
            print(e)
            Main_process.user_com.send(Config.ERROR)
