import socket 
import time
import random

receiver_host = '127.0.0.1'
receiver_port = 10080
receiver_addr = (receiver_host, receiver_port)
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

packet = []
recv_buffer = []
ack = -1
cum_ack = -1
start_t = 0
log_name = ''

def logger(logargs, log_name):
    flog = open(log_name, 'a')
    flog.write(logargs)
    flog.close()

def recv_and_ack(packet_loss):
    global packet, recv_buffer, ack, cum_ack, start_t, log_name     
    
    while True:
        msg, sender_addr = receiver_socket.recvfrom(4096)
        now = time.time() - start_t
        if msg[:1].decode() == '0':
            msg = msg.decode()
            msg_split = msg.split("|")
            file_name, packet_num, start_t = msg_split[1], int(msg_split[2]), float(msg_split[3])
            log_name = file_name + '_receiving_log.txt'
            flog = open(log_name, 'w+')
            packet = [None] * packet_num
            recv_buffer = [None] * packet_num

        elif msg[:1].decode() == '1':
            header = msg[:7].decode()
            seq = int(header.split("|")[1])
            data = msg[7:]
            p = random.random()

            if (p < packet_loss):
                logger("{:.3f} pkt: {:d}\t| arrived but dropped \n".format(now, seq), log_name)
            else:
                now = time.time() - start_t
                if seq == ack+1 :
                    packet[seq] = data
                    if ack == cum_ack:
                        cum_ack +=1
                    ack += 1
                    if ack < cum_ack:
                        if None not in recv_buffer[ack+1: cum_ack+1]:
                            for i in range(ack+1, cum_ack+1):
                                packet[i] = recv_buffer[i]
                            ack = cum_ack
                    logger("{:.3f} pkt: {:d}\t| received\n".format(now, seq), log_name)
                    logger("{:.3f} ACK: {:d}\t| sent\n".format(now, ack), log_name)
                    msg = b'%5d'%(ack) + "|".encode()
                    receiver_socket.sendto(msg, sender_addr)         
                elif seq > ack+1:
                    recv_buffer[seq] = data
                    cum_ack = seq
                    logger("{:.3f} pkt: {:d}\t| received\n".format(now, seq), log_name)
                    logger("{:.3f} ACK: {:d}\t| sent\n".format(now, ack), log_name)
                    msg = b'%5d'%(ack) + "|".encode()
                    receiver_socket.sendto(msg, sender_addr)
             

        elif msg[:1].decode() == '2':
            with open(file_name, 'wb') as f:
                for i in range(packet_num):
                    f.write(packet[i]) 
            logger("File transfer is finished.\n", log_name)
            logger("Throughput: {:.2f} pkts / sec\n".format(packet_num/now), log_name)
            return True

if __name__ == "__main__":
    
    packet_loss = float(input("packet loss probability: "))
    
    print("socket recv buffer size: ", receiver_socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
    receiver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000)
    print("socket recv buffer size updated: ", receiver_socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
    receive_done = False
    print()
    receiver_socket.bind(receiver_addr)
    while not receive_done:
        try:
            print("receiver program starts...")
            receive_done = recv_and_ack(packet_loss)
        except KeyboardInterrupt:
            break