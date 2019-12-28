import os
import datetime
import socket
import threading

client_host = socket.gethostname
client_port = 10008
client_addr = (client_host, client_port)
server_host = '127.0.0.1'
server_addr = (server_host, 10080)

class Cmd_handler():

    def __init__(self, tcp_conn, udp_conn, cid):
        self.tcp_conn = tcp_conn
        self.udp_conn = udp_conn
        self.cid = cid
        self.tcp_msg = None
        self.upd_msg = None
        self.tcp_recv_thread = threading.Thread(target = self.tcp_receiver)
        self.tcp_recv_thread.start()
        self.udp_recv_thread = threading.Thread(target = self.ucp_receiver)
        self.udp_recv_thread.start()

    def tcp_receiver(self):
        while True:
            recv_msg, recv_addr = self.tcp_conn.recvfrom(4096)
            self.tcp_msg = recv_msg.decode()
            if(self.tcp_msg[0] == '#'):
                addr = self.tcp_msg.split("|")
                dst_ip = addr[0][1:]
                dst_port = int(addr[1])
                chat_msg = addr[2]
                self.udp_conn.sendto(chat_msg.encode(), (dst_ip, dst_port))
            else:
                print(recv_msg.decode())

    def ucp_receiver(self):
        while True:
            recv_msg, recv_addr = self.udp_conn.recvfrom(4096)
            self.upd_msg = recv_msg.decode()
            print(self.upd_msg)
  

    def run(self, cmd):
        self.cmd = cmd
        if self.cmd[0] != '@':
            return
        tmp_cmd = self.cmd[1:].split(" ")
        request = tmp_cmd[0]
        if request == "show_list":
            msg = "1|" + self.cid + "|" + request
            self.tcp_conn.send(msg.encode())
        elif request == 'awake':
            msg = "1|" + self.cid + "|" + request
            self.tcp_conn.send(msg.encode())
        elif request == 'exit':
            msg = "3|" + self.cid
            self.tcp_conn.send(msg.encode())
            return
        elif request == 'chat':
            dst_id = tmp_cmd[1]
            msg_to_send = ' '.join(tmp_cmd[2:])
            chat_msg = "From {src_id} [{cmsg}]".format(src_id=self.cid, cmsg=msg_to_send)
            msg = "2|" + self.cid + "|" + dst_id + "|" + chat_msg
            self.tcp_conn.send(msg.encode())


def client():
    client_ID = input("Input Your ID : ")
    server_host = input("input server's IP address : ")
    server_addr = (server_host, 10080)
    tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_client.connect(server_addr)
    done = False
     
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_client.bind(('', 0)) 
    udp_port = udp_client.getsockname()[1]

    msg = "0|" + client_ID + "|" + str(udp_port)
    tcp_client.send(msg.encode())
    recv_msg = tcp_client.recv(2048)
    print(recv_msg.decode())
    cmd_handler = Cmd_handler(tcp_client, udp_client, client_ID)
        
    try:
        #tcp_client.listen(200)
        while not done:
            cmd = input()
            cmd_handler.run(cmd)
            if cmd == '@exit':
               done = True
                  
    except KeyboardInterrupt:
        tcp_client.close()



if __name__ == '__main__':
    client()  
