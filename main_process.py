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
    def __init__(self):
        self.a = 0
        self.gfbase = 29
        self.gfbound = 2**8
        self.gfilog = self._gfilog()
        self.gflog = self._gflog()

    def connect(self, ip, ports_for_storage, port_for_user):
        storage_com_ser = Communication(ip, ports_for_storage, is_server=True, for_user=False)
        user_com_ser = Communication(ip, port_for_user, is_server=True, for_user=True)
        return storage_com_ser, user_com_ser

    def coefficient(self, index):
        if 2**index < self.gfbound:
            return 2**index
        elif 2**index >= self.gfbound:
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
    def parties_renew(self, storages, block_id):
        blocks = list()
        coeffs = list()
        for st_id in range(Config.SS):
            blocks.append(storages[st_id].read(block_id))
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

        return p_block, q_block

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
                    data2 = data2 ^ self._gf_product(blocks[j][i], coeffs[j]) ^\
                            self._gf_product(blocks[j][i], corp_coeff1)
                    data1 = data1 ^ blocks[j][i]
                data2 = data2 ^ self._gf_product(p_block[i], corp_coeff1) ^ q_block[i]
                data2 = self._gf_div(data2, corp_coeff1 ^ corp_coeff2)
                recover2.append(data2)

                data1 ^= data2 ^ p_block[i]
                recover1.append(data1)
            return [recover1, recover2]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Main Process')
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

    # my_ip is used for localhost test
    # it will first wait all storage processes to connect
    # then it will wait user process to connect, then it will listen to user's command
    storage_com, user_com = Main_process.connect(my_ip, args.storage_port, args.user_port)

    while True:
        command = user_com.receive()
        if command == 'upload':
            filename = user_com.receive()
            contents = user_com.receive()
            # write contents to storage process

        elif command == 'download':
            filename = user_com.receive()
            # find the contents of filename from storage process

        elif command == 'delete':
            filename = user_com.receive()
        else:
            chaos = user_com.receive()
            user_com.send(Config.ERROR)
            raise Exception