import math
import sys
import struct

class Config:
    def __init__(self):
        self.BS = 16  # block size in kilobytes
        self.BN = 1024  # block number of each storage
        self.RBFM = 4  # reverse block number for save file name and other information, used by main process, first RBFM
        self.RBFS = 2  # reverse block number for storage process to save which blocks are used, after RBFM then RBFS
        assert self.BS * 1024 < 4294967295
        self.BFI = len(struct.pack('I', self.BS*1024))
