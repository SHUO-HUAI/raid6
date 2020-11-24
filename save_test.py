import os
import struct

from config import Config

def read_block():
    # return -1
    all_centent = []
    for i in range(4):
        p = os.path.join('./imgs', str(i) + '.bin')
        read_b = open(p, "rb")
        data = read_b.read()
        # print(len(data))

        length = int(struct.unpack('I', data[:Config.BFI])[0])
        content = data[Config.BFI:length + Config.BFI]
        all_centent.append(content)

    write = open('./imgs/read_2.png', 'wb')
    for c in all_centent:
        write.write(c)


def write_block(PATH1, PATH2):
    i = 0
    read_b = open(PATH2, "rb")

    while True:
        content1 = read_b.read(Config.BS - Config.BFI)

        if len(content1) == 0:
            break
        else:
            p = os.path.join(PATH1, str(i) + '.bin')
            fr = open(p, "rb")
            data = fr.read()
            writh_b = open(p, "wb")
            writh_b.write(data)
            length = struct.pack('I', len(content1))
            writh_b.seek(0x0)
            writh_b.write(length)
            writh_b.write(content1)
            writh_b.flush()
            fr.close()
            writh_b.close()
        i = i + 1
    read_b.close()
    
    
    
    
#
i = 0

while i < 6:

    p = os.path.join('./imgs', str(i) + '.bin')
    writh_b = open(p, "wb")
    for k in range(Config.BS):
        writh_b.write(b'\x00')
    writh_b.flush()
    writh_b.close()
    i = i + 1
# exit()
write_block('./imgs/', './imgs/aa.png')

read_block()