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


class Main:
    def __init__(self, ip, ports_for_storage, port_for_user):
        self.a = 0
        self.gfbase = 29
        self.gfbound = 2 ** 8
        self.gfilog = self._gfilog()
        self.gflog = self._gflog()

        storage_com_ser = Communication(ip, ports_for_storage, is_server=True, for_user=False)
        # user_com_ser = Communication(ip, port_for_user, is_server=True, for_user=True)
        user_com_ser = None
        self.storage_ser = storage_com_ser
        self.usr_com = user_com_ser
        self.ports_for_storage = ports_for_storage

        self.write_finish = False  # used for record a file if finishing writing
        self.write_record_tmp = []  # used for tmp save write information
        self.all_record_files = {}  # record all save files, including the filename and storage location, save down when shutdown

    def coefficient(self, index):
        if 2 ** index < self.gfbound:
            return 2 ** index
        elif 2 ** index >= self.gfbound:
            coeff = 2 * self.coefficient(index - 1)
            if coeff < self.gfbound:
                return coeff
            else:
                return coeff ^ self.gfbound ^ self.gfbase

    def _gfilog(self):
        ilog = np.zeros(self.gfbound)
        for idx in range(self.gfbound - 1):
            ilog[idx] = self.coefficient(idx)
        return ilog

    def _gflog(self):
        log = np.zeros(self.gfbound)
        for idx in range(self.gfbound):
            log[int(self.gfilog[idx])] = idx
        return log

    def _gf_product(self, x, k):
        return self.gfilog[(self.gflog[x] + self.gflog[k]) // 255]

    def _gf_div(self, x, k):
        return self.gfilog[(self.gflog[x] - self.gflog[k] + 255) // 255]

    '''
    inputs: storages: lists of all storage processes; block_id: the block_id to write data
    outputs: p_block: renewed block (corresponding to block_id) of P party; q_block renewed block of Q party 
    '''

    def parties_renew(self, contents):
        for c_i in contents:
            print(c_i)
        blocks = list()
        coeffs = list()
        assert len(contents) == Config.SS  # this line need to be modified when some storage shutdown
        for st_id in range(Config.SS):
            # blocks.append(storages[st_id].read(block_id))  # contents
            blocks.append(contents[st_id])
            coeffs.append(self.gfilog[st_id])

        p_block = list()
        q_block = list()
        for i in range(Config.BS):
            p_check = 0
            q_check = 0
            for j in range(Config.SS):
                data = blocks[j][i]
                p_check = p_check ^ data
                q_check = q_check ^ self._gf_product(data, coeffs[j])
            p_block.append(p_check)
            q_block.append(q_check)

        return p_block, q_block  # contents

    '''
    input: storages: ...; corrupt_id: the storage process you use; block_id: the block you read
    output:  recover_block: recovered data block
    '''

    def read_recover(self, storages, corrupt_id, block_id):
        blocks = list()
        # for P party
        p_id = Config.SN - 2
        # the last storage for Q party
        q_id = Config.SN - 1
        corrupt_ids = [corrupt_id]
        recover_block = list()
        coeffs = list()

        # check all corrupted storages
        for st_id in range(Config.SN):
            if st_id != corrupt_ids:
                block = storages[st_id].read(block_id)
                if block == Config.ERROR:
                    corrupt_ids.append(st_id)
                else:
                    blocks.append(block)

        # get coefficients of data storages
        for coeff_id in range(Config.SS):
            coeffs.append(self.gfilog[coeff_id])

        # only one data storage corrupts
        if len(corrupt_ids) == 1:
            for i in range(Config.BS):
                data = 0
                for j in range(len(blocks) - 1):
                    data = data ^ blocks[j][i]
                recover_block.append(data)
            return recover_block
        # one data storage and Q storage corrupt
        elif q_id in corrupt_ids:
            for i in range(Config.BS):
                data = 0
                for j in range(len(blocks)):
                    data = data ^ blocks[j][i]
                recover_block.append(data)
            return recover_block
        # one data storage and P storage corrupt
        elif p_id in corrupt_ids:
            corrupt_coeff = coeffs.pop(corrupt_id)
            for i in range(Config.BS):
                data = 0
                for j in range(Config.SS - 1):
                    data = data ^ self._gf_product(blocks[j][i], coeffs[j])
                data = data ^ blocks[-1][i]
                data = self._gf_div(data, corrupt_coeff)
                recover_block.append(data)
            return recover_block
        # two data storages corrupt
        elif p_id not in corrupt_ids and q_id not in corrupt_ids:
            p_block = blocks[-2]
            q_block = blocks[-1]
            recover1, recover2 = list(), list()
            corp_coeff1, corp_coeff2 = coeffs.pop(corrupt_ids[0]), coeffs.pop(corrupt_ids[1])

            for i in range(Config.BS):
                data1, data2 = 0, 0
                for j in range(Config.SS - 2):
                    data2 = data2 ^ self._gf_product(blocks[j][i], coeffs[j]) ^ \
                            self._gf_product(blocks[j][i], corp_coeff1)
                    data1 = data1 ^ blocks[j][i]
                data2 = data2 ^ self._gf_product(p_block[i], corp_coeff1) ^ q_block[i]
                data2 = self._gf_div(data2, corp_coeff1 ^ corp_coeff2)
                recover2.append(data2)

                data1 ^= data2 ^ p_block[i]
                recover1.append(data1)
            return [recover1, recover2]

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
                free_blocks_each_stroage.append(free_blocks)
            free_blocks_each_stroage = np.array(free_blocks_each_stroage)

            print(free_blocks_each_stroage)
            storage_id = free_blocks_each_stroage.argmax()  # save content to the most empty storage
            print(storage_id)

            self.storage_ser.send(Config.Write_storage, storage_id)  # write commend
            self.storage_ser.send('None', storage_id)  # block id
            self.storage_ser.send(content, storage_id)  # content
            block_id = self.storage_ser.receive(storage_id)
            assert block_id != Config.ERROR
            self.write_record_tmp.append([storage_id, block_id])

            # for computing p q
            all_contents_for_pq = []
            for s_id in range(Config.SS):
                self.storage_ser.send(Config.Read_storage, s_id)  # read commend
                self.storage_ser.send(block_id, s_id)  # read block
                content_read = self.storage_ser.receive(s_id)
                all_contents_for_pq.append(content_read)
            p_block, q_block = self.parties_renew(all_contents_for_pq)
            print(p_block)
            print(q_block)

            # for writing p q
            self.storage_ser.send(Config.Write_storage, Config.SS)  # write commend for p
            self.storage_ser.send(block_id, Config.SS)  # write block id
            self.storage_ser.send(p_block, Config.SS)
            self.storage_ser.receive(Config.SS)

            self.storage_ser.send(Config.Write_storage, Config.SS + 1)  # write commend for p
            self.storage_ser.send(block_id, Config.SS + 1)  # write block id
            self.storage_ser.send(q_block, Config.SS + 1)
            self.storage_ser.receive(Config.SS + 1)

        else:
            assert filename not in self.all_record_files.keys()
            self.all_record_files[filename] = np.array(self.write_record_tmp)
            self.write_record_tmp = []
            self.write_finish = False

    def read(self, filename):
        pass

    def delete(self, filename):
        pass

    def modify(self, filename):
        pass

    def ping(self):
        # ping is used to guarantee all storage is connected
        broken_ids = []
        for s_id in range(Config.SN):
            SUCC = self.storage_ser.send(Config.Ping_storage, s_id)
            if SUCC:
                self.storage_ser.receive(s_id)
                print(str(s_id) + ' is alive')
            else:
                print(str(s_id) + ' is shutdown')
                broken_ids.append(s_id)
        if len(broken_ids) > 0:
            self.storage_ser.hock_for_broken(broken_ids)


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
    i = 0
    while True:
        k = input()
        if int(k) == 0:
            break

        read_b = open("./imgs/Distributed system project 2020.docx", "rb")
        Main_process.write_finish = False
        name = "./imgs/test" + str(i)
        while True:
            content1 = read_b.read(Config.BS - Config.BFI)  # a content is a block size - information size
            if len(content1) == 0:
                break
            else:
                Main_process.write(content1)
        read_b.close()

        i = i + 1
        Main_process.write_finish = True
        Main_process.write(0, name)
        print(Main_process.all_record_files)

    # while True:
    #     command = user_com.receive()
    #     if command == 'upload':
    #         filename = user_com.receive()
    #         contents = user_com.receive()
    #         # write contents to storage process
    #
    #     elif command == 'download':
    #         filename = user_com.receive()
    #         # find the contents of filename from storage process
    #
    #     elif command == 'delete':
    #         filename = user_com.receive()
    #     else:
    #         chaos = user_com.receive()
    #         user_com.send(Config.ERROR)
    #         raise Exception
