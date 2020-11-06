import math


class Config:
    def __init__(self):
        self.BS = 32  # block size in kilobytes
        self.BN = 1024  # block number of each storage
        self.RBFM = 4  # reverse block number for save file name and other information, used by main process, first RBFM
        self.RBFS = 2  # reverse block number for storage process to save which blocks are used, after RBFM then RBFS
        self.BFI = round(math.log(self.BS * 1024 * 8, 2))  # bits in each block used for save this block contents length
