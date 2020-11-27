import struct


class Config:
    BS = 16 * 1024  # block size in bytes
    BN = 16  # block number of each storage
    RBFM = 4  # reverse block number for save file name and other information, used by main process, first RBFM
    RBFS = 1  # reverse block number for storage process to save which blocks are used, after RBFM then RBFS
    BFI = len(struct.pack('I', 1))
    assert BS < 4294967295
    assert BN < RBFS * BS / BFI
    assert BS % BFI == 0

    SN = 4  # total storage process number
    SP = 2  # parities number
    SS = SN - SP  # for storage

    assert SP == 2

    ERROR = 4294967295  # as all stuck pack we used is unsigned int, so we use 4294967295 for error
    SUCC = 1

    # commend
    Free_blocks = 'Looking up empty block amount...'
    Write_storage = 'Writing storage data...'
    Write_storage_For_p = 'writing storage data with length...'
    Read_storage = 'Reading storage data...'
    Read_storage_For_p = 'read storage data with length...'
    Ping_storage = 'Ping storage...'
    Delete_block = 'Deleting block...'

    Write_For_User = 'upload'
    Read_For_User = 'download'
    Delete_For_User = 'delete'
    Modify_For_User = 'modify'
    Write_done = 'done'
