import os
import datetime
import socket 
import threading

####### server ip 입력 #######
server_host = '127.0.0.1'  
#############################
server_port = 10080
server_addr = (server_host, server_port)

'''
udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind(server_addr)
'''
threads = []

client_status = ['Asleep', 'Awake']
clients = {} # { client_id: (status, ip, port) }

class Client_thread(threading.Thread):

    def __init__(self, ip, port, tcp_conn):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.tcp_conn = tcp_conn

    def run(self):
        client_id = ""
        while True:
            try:
                # num | client_id | cmd |
                recv_msg = self.tcp_conn.recv(4096)
                if not recv_msg:
                    print("{id} is disconnected".format(id=client_id))
                    del clients[client_id]
                    break
                recv_msg = recv_msg.decode()    
                cmd = recv_msg.split("|")
                client_id = cmd[1]
                if cmd[0] == '0':
                    clients[client_id] = [client_status[0], self.ip, int(cmd[2])]
                    print("{} {}".format(client_id, clients[client_id][0]))
                    msg = self.get_list()
                    self.tcp_conn.send(msg.encode())
                
                # show_list, awake
                elif cmd[0] == '1':
                    request = cmd[2]
                    if request == 'awake':
                        clients[client_id][0] = client_status[1]
                        msg= "{id} {status} {ip}:{port}\n".format(
                            id = client_id, status = clients[client_id][0],
                            ip = clients[client_id][1], port = clients[client_id][2])
                        print(msg)
                    elif request == 'show_list':
                        msg = self.get_list()
                        self.tcp_conn.send(msg.encode())
                                    
                elif cmd[0] == '2':
                    src_id = cmd[1]
                    if src_id in clients:
                        if clients[src_id][0] == client_status[0]:
                            clients[src_id][0] = client_status[1]
                            msg= "{id} {status} {ip}:{port}\n".format(
                                id = src_id, status = clients[src_id][0],
                                ip = clients[src_id][1], port = clients[src_id][2])
                            print(msg)
                    dst_id = cmd[2]
                    msg_to_send = cmd[3]
                    if dst_id in clients:
                        if clients[dst_id][0] == 'Awake':
                            msg = "#{ip}|{port}|{msg}".format(
                                ip = clients[dst_id][1], port = clients[dst_id][2],
                                msg = msg_to_send)
                            self.tcp_conn.send(msg.encode())
                
                elif cmd[0] == '3':
                    print("{id} is unregistered".format(id=client_id))
                    del clients[client_id]
                    break

            
            except socket.error as msg:
                print("error occured : ", msg)
        self.tcp_conn.close()
        return

    def get_list(self):
        msg = ""
        for client in clients:
            if clients[client][0] == 'Awake':
                msg += "{id} {status} {ip}:{port}\n".format(
                            id = client, status = clients[client][0],
                            ip = clients[client][1], port = clients[client][2])
            else:
                msg += "{id} {status}\n".format(
                            id = client, status = clients[client][0])
        return msg


def server():
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(server_addr)
    print("server starts on ip : {}".format(server_host))
    try:
        tcp_server.listen(200)
        while True:
            connection_socket, (ip, port) = tcp_server.accept()
            new_thread = Client_thread(ip, port, connection_socket)
            new_thread.start()

    except KeyboardInterrupt:
        tcp_server.close()


if __name__ == '__main__':
    server()  
