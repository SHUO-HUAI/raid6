import argparse
import os
import random
import socket
import sys
from datetime import datetime
from config import Config
import struct
from communication import Communication


class User:
    def __init__(self, host_ip, port):
        self.com_ser = Communication(host_ip, port, is_server=False, for_user=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='User Process')
    parser.add_argument('--ip', default='127.0.0.1', type=str, help='main process ip address (default: localhost)')
    parser.add_argument('--user_port', default=12346, type=int, help='main process ports for user process')
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

    User_process = User(my_ip, args.user_port)
    while True:
        try:
            instruction = input().split()
            # assert len(instruction) == 2
            if len(instruction) != 2:
                raise RuntimeError
            commend = instruction[0]
            filename = instruction[1]
            User_process.com_ser.send(commend)
            User_process.com_ser.send(filename)

            if commend == Config.Write_For_User:
                all_content = []
                read_b = open(filename, "rb")
                while True:
                    content1 = read_b.read(Config.BS - Config.BFI)  # a content is a block size - information size
                    if len(content1) == 0:
                        break
                    else:
                        all_content.append(content1)
                read_b.close()
                User_process.com_ser.send(commend)
                User_process.com_ser.send(all_content)

            elif commend == Config.Read_For_User:
                all_centent = User_process.com_ser.receive()
                folder = './download_from_server'
                if not os.path.exists(folder):
                    os.makedirs(folder)
                file = filename.split('/')[-1]
                write = open(os.path.join(folder, file), 'wb')
                # for c in all_centent:
                write.write(all_centent)
                write.close()

            elif commend == Config.Delete_For_User:
                pass

            elif commend == Config.Modify_For_User:
                all_content = []
                read_b = open(filename, "rb")
                while True:
                    content1 = read_b.read(Config.BS - Config.BFI)  # a content is a block size - information size
                    if len(content1) == 0:
                        break
                    else:
                        all_content.append(content1)
                read_b.close()
                User_process.com_ser.send(commend)
                User_process.com_ser.send(all_content)
            else:
                print('unknown commend, support only:', Config.Write_For_User, Config.Read_For_User,
                      Config.Delete_For_User, Config.Modify_For_User)

        except BrokenPipeError as e:
            print(e)
        except FileNotFoundError as e:
            print(e)
        except RuntimeError as e:
            print(e)
            print('instructions length must equals to 2')
