import pickle
import socket
import struct
import sys

from config import Config


class Communication:
    def __init__(self, server_ip=None, server_ports=(9999, 9998, 9997, 9996, 9995, 9994), is_server=False):
        self.comm = []
        assert len(server_ports) == Config.SN
        if is_server:
            self.comm = []
            try:
                skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                skt.connect(('8.8.8.8', 80))
                socketIpPort = skt.getsockname()
                my_ip = socketIpPort[0]
                skt.close()
            except socket.error as msg:
                print(msg)
                sys.exit(1)

            try:
                for server_port in server_ports:
                    print('Waiting for another {} storage processes'.format(Config.SN - len(self.comm)))
                    socketser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    socketser.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    socketser.bind((my_ip, server_port))
                    socketser.listen(1)
                    conn, addr = socketser.accept()
                    self.comm.append(conn)
            except socket.error as msg:
                print(msg)
                sys.exit(1)
            print('all storage are connected')

        else:
            assert server_ip is not None

            for server_port in server_ports:
                try:
                    sclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sclient.connect((server_ip, server_port))
                    self.comm = [sclient]
                    break
                except socket.error as msg:
                    if server_port == server_ports[-1]:
                        print(msg)

        assert len(self.comm) > 0

    # storage id is used by main process to identify which storage process to write in.
    # for storage process, as it is client, it only connect to a server, so no storage id is needed
    def send(self, contents, storage_id=None):
        if storage_id is not None:
            comm = self.comm[storage_id]
        else:
            comm = self.comm[0]
        try:
            all_data = pickle.dumps(contents)
            num = len(all_data)
            gotten = struct.pack('I', num)
            comm.send(gotten)

            gg = 0

            while 1:
                if gg + 1024 < num:
                    data = all_data[gg:gg + 1024]
                    comm.send(data)
                else:
                    data = all_data[gg:num]
                    comm.send(data)
                    break
                gg = gg + 1024
                file_info_size = struct.calcsize('I')
                buf = comm.recv(file_info_size)
        except BrokenPipeError as e:
            print(str(storage_id) + ' has been broken!!')
            # del self.comm[storage_id]
            return -1  # need to be record by main process, then re-construct
        return 1

    # storage id is used by main process to identify which storage process to read from
    def receive(self, storage_id=None):

        if storage_id is not None:
            comm = self.comm[storage_id]
        else:
            comm = self.comm[0]

        num = 0
        file_info_size = struct.calcsize('I')
        buf = comm.recv(file_info_size)
        if buf:
            gotten = struct.unpack('I', buf)
            num = gotten[0]
        all_data = b''
        gg = 0
        while 1:
            try:
                if gg + 1024 < num:
                    data = comm.recv(1024)
                    all_data = all_data + data
                else:
                    data = comm.recv(num - gg)
                    all_data = all_data + data
                    break
                gg = gg + 1024
                gotten = struct.pack('I', 1)
                comm.send(gotten)
            except Exception as e:
                print(e)
                comm.close()
                exit()
        try:
            recv_message = pickle.loads(all_data)
            return recv_message
        except Exception as e:
            print(e)
            comm.close()
            exit()


if __name__ == '__main__':

    try:
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.connect(('8.8.8.8', 80))
        socketIpPort = skt.getsockname()
        my_ip = socketIpPort[0]
        skt.close()
    except socket.error as msg:
        print(msg)
        sys.exit(1)

    is_s = int(input())
    C = Communication(is_server=is_s == 1, server_ip=my_ip)
    while True:
        if is_s:
            a = input()
            for i in range(Config.SN):
                r = C.send(a + ' to ' + str(i), i)
                if r != -1:
                    b = C.receive(i)
                    print(b)
        else:
            b = C.receive()
            print(b)
            C.send(1)
