import struct


class Config:
    BS = 16 * 1024  # block size in kilobytes
    BN = 1024  # block number of each storage
    RBFM = 4  # reverse block number for save file name and other information, used by main process, first RBFM
    RBFS = 1  # reverse block number for storage process to save which blocks are used, after RBFM then RBFS
    BFI = len(struct.pack('I', 1))
    assert BS < 4294967295
    assert BN < RBFS * BS / BFI
    assert BS % BFI == 0

    SN = 6  # storage process number
    SP = 2  # parities number
    SS = SN - SP  # for storage
