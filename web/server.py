import socket
import threading
import time

cli_sd_TCP = []
# cli_sd_UDP = []
# def TCP(s):
"""
def UDP(s):
    while True:
        data = b''
        while True:
            temp, addr = s.recvfrom(1024)

            if temp == b'|END|':
                break

            if addr not in cli_sd_UDP:
                cli_sd_UDP.append(addr)
                print('Connected by', addr)

            data += temp

            for other in cli_sd_UDP:
                if other is not addr:
                    other.sendall(data)
                    other.sendall(b'|END|')
"""


def receive_message_TCP(client):
    while True:
        data = b''
        try:
            while True:
                temp = client.recv(1024)

                if temp == b'|END|':
                    break

                if temp == b'|EXIT|':
                    print("client exit")
                    cli_sd_TCP.remove(client)
                    client.close()
                    break

                data += temp

            if data:
                print('recv from client')
                try:
                    for other in cli_sd_TCP:
                        if other is not client:
                            other.sendall(data)
                            other.sendall(b'|END|')

                except:
                    pass
        except:
            pass


HOST = str(input('IP: '))
PORT_TCP = int(input('PORT: '))
# PORT_UDP = 1268
s_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s_TCP.bind((HOST, PORT_TCP))
# s_UDP.bind((HOST, PORT_UDP))
s_TCP.listen(1)
print("server is running")
while True:
    conn, addr = s_TCP.accept()
    print('Connected by', addr)
    cli_sd_TCP.append(conn)
    threading.Thread(target=receive_message_TCP, args=(conn,)).start()
# threading.Thread(target=TCP, args=(s_TCP,)).start()
# threading.Thread(target=UDP, args=(s_UDP,)).start()
