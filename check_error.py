import numpy as np
from copy import deepcopy

from config import Config


def bitwise_xor_bytes(a, b):
    result_int = int.from_bytes(a, byteorder="big") ^ int.from_bytes(b, byteorder="big")
    return result_int.to_bytes(max(len(a), len(b)), byteorder="big")


class Verifier:

    def __init__(self):
        self.gfbase = 29
        self.gfbound = 2 ** 8
        self.gfilog = self._gfilog()
        self.gflog = self._gflog()
        self.p_id = Config.SN - 2
        self.q_id = Config.SN - 1

    def recover(self, broken_storage_ids, all_contents: dict):
        assert len(broken_storage_ids) <= 2
        new_contents = deepcopy(all_contents)
        coeffs = []

        # get coefficients of data storages
        for st_id in range(Config.SS):
            coeffs.append(self.gfilog[st_id])

        # only one storage corrupted
        if len(broken_storage_ids) == 1:
            broken_id = broken_storage_ids[0]
            # data storage
            if broken_id < Config.SS:
                self._recover_data_from_p(broken_id, new_contents)
            # P storage
            elif broken_id == self.p_id:
                self._recover_p(new_contents)
            # Q storage
            elif broken_id == self.q_id:
                self._recover_q(new_contents, coeffs)
        # two storage corrupted
        elif len(broken_storage_ids) == 2:
            # P storage and Q storages
            if self.p_id in broken_storage_ids and self.q_id in broken_storage_ids:
                self._recover_p(new_contents)
                self._recover_q(new_contents, coeffs)
            # data storage and P storage
            elif self.p_id in broken_storage_ids and self.q_id not in broken_storage_ids:
                data_id = min(broken_storage_ids)
                self._recover_data_from_q(data_id, new_contents, coeffs)
                self._recover_p(new_contents)
            # data storage and Q storage
            elif self.q_id in broken_storage_ids and self.p_id not in broken_storage_ids:
                data_id = min(broken_storage_ids)
                self._recover_data_from_p(data_id, new_contents)
                self._recover_q(new_contents, coeffs)
            # two data storage
            elif self.q_id not in broken_storage_ids and self.p_id not in broken_storage_ids:
                coeff_a = coeffs[broken_storage_ids[0]]
                coeff_b = coeffs[broken_storage_ids[1]]
                for blk_id in range(Config.BN):
                    recover_a = []
                    recover_b = []
                    for i in range(Config.BS):
                        data_a = b'\x00'
                        data_b = b'\x00'
                        for j in range(Config.SS):
                            if j not in broken_storage_ids:
                                data_a = bitwise_xor_bytes(data_a, new_contents[[j, blk_id]][i])
                                data_b = bitwise_xor_bytes(data_b, self._gf_product(new_contents[[j, blk_id]][i],
                                                                                    coeffs[j]))
                                data_b = bitwise_xor_bytes(data_b, self._gf_product(new_contents[[j, blk_id]][i],
                                                                                    coeff_a))
                        data_b = bitwise_xor_bytes(data_b, self._gf_product(new_contents[[self.p_id, blk_id]][i],
                                                                            coeff_a))
                        data_b = bitwise_xor_bytes(data_b, new_contents[[self.q_id, blk_id]][i])
                        data_b = self._gf_div(data_b, bitwise_xor_bytes(coeff_a, coeff_b))
                        recover_b.append(data_b)

                        data_a = bitwise_xor_bytes(data_a, data_b)
                        data_a = bitwise_xor_bytes(data_a, new_contents[[self.p_id, blk_id]][i])
                        recover_a.append(data_a)

                    new_contents[[broken_storage_ids[0], blk_id]] = recover_a
                    new_contents[[broken_storage_ids[1], blk_id]] = recover_b

        return new_contents

    def _recover_p(self, contents):
        for blk_id in range(Config.BN):
            recover_block = []
            for i in range(Config.BS):
                p_check = b'\x00'
                for j in range(Config.SS):
                    p_check = bitwise_xor_bytes(p_check, contents[[j, blk_id]][i])
                recover_block.append(p_check)
            contents[[self.p_id, blk_id]] = recover_block

    def _recover_q(self, contents, coeffs):
        for blk_id in range(Config.BN):
            recover_block = []
            for i in range(Config.BS):
                q_check = b'\x00'
                for j in range(Config.SS):
                    q_check = bitwise_xor_bytes(q_check, self._gf_product(contents[[j, blk_id]][i], coeffs[j]))
                recover_block.append(q_check)
            contents[[self.q_id, blk_id]] = recover_block

    def _recover_data_from_p(self, data_id, contents):
        for blk_id in range(Config.BN):
            recover_block = []
            for i in range(Config.BS):
                data = b'\x00'
                for j in range(Config.SS):
                    if j != data_id:
                        data = bitwise_xor_bytes(data, contents[[j, blk_id]][i])
                data = bitwise_xor_bytes(data, contents[[self.p_id, blk_id]][i])
                recover_block.append(data)
            contents[[data_id, blk_id]] = recover_block

    def _recover_data_from_q(self, data_id, contents, coeffs):
        for blk_id in range(Config.BN):
            recover_block = []
            for i in range(Config.BS):
                data = b'\x00'
                for j in range(Config.SS):
                    if j != data_id:
                        data = bitwise_xor_bytes(data, self._gf_product(contents[[j, blk_id]][i], coeffs[j]))
                data = bitwise_xor_bytes(data, contents[self.q_id])
                data = self._gf_div(data, coeffs[data_id])
                recover_block.append(data)
            contents[[data_id, blk_id]] = recover_block

    def _gfilog(self):
        ilog = np.empty(self.gfbound, dtype=np.uint8)
        for idx in range(self.gfbound - 1):
            ilog[idx] = self.coefficient(idx)
        return ilog

    def _gflog(self):
        log = np.empty(self.gfbound, dtype=np.uint8)
        for idx in range(self.gfbound):
            log[int(self.gfilog[idx])] = idx
        return log

    def _gf_product(self, x, coeff):
        if isinstance(x, bytes):
            x = int.from_bytes(x, byteorder="big")
        if isinstance(coeff, bytes):
            coeff = int.from_bytes(coeff, byteorder="big")
        #
        # print((self.gflog[x], self.gflog[coeff], self.gfilog[(self.gflog[x] + self.gflog[coeff]) % 255]))
        # input()
        return bytes([self.gfilog[(self.gflog[x] + self.gflog[coeff]) % 255]])

    def _gf_div(self, x, coeff):
        if isinstance(x, bytes):
            x = int.from_bytes(x, byteorder="big")
        if isinstance(coeff, bytes):
            coeff = int.from_bytes(coeff, byteorder="big")
        return bytes([self.gfilog[(self.gflog[x] - self.gflog[coeff] + 255) % 255]])

    def coefficient(self, index):
        if 2 ** index < self.gfbound:
            return 2 ** index
        elif 2 ** index >= self.gfbound:
            coeff = 2 * self.coefficient(index - 1)
            if coeff < self.gfbound:
                return coeff
            else:
                return coeff ^ self.gfbound ^ self.gfbase
