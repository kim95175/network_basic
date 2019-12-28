import socket 
import os
import threading
import time


packet_size = 1024
send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

packet = []
packet_timer = []
packet_size = 1024
start_t = time.time()
done = False
nextseqnum = 0
base = 0
ack = 0
log_name = ''


def logger(logargs, log_name):
    flog = open(log_name, 'a')
    flog.write(logargs)
    flog.close()

def msg_preprocess(seq_num):
    msg = "1|".encode() + b'%5d'%(seq_num)

    return msg

def send_packet(file_name, packet_num, receiver_addr, window_size, time_out):
    global packet, packet_timer, start_t, done, nextseqnum, base, log_name
    while True:
        with threading.Lock():
            now = time.time() - start_t
            tmp_window_size = (base + window_size) if (base + window_size) <= packet_num else packet_num
            if (nextseqnum < tmp_window_size) :     
                msg = msg_preprocess(nextseqnum)
                packet_timer[nextseqnum] = now
                logger("{:.3f} pkt: {}\t| Sent\n".format(now, nextseqnum), log_name)
                send_socket.sendto(msg + packet[nextseqnum], receiver_addr) 
                nextseqnum += 1
            
            for i in range(base, nextseqnum):
                time_after_send = now - packet_timer[i]
                if (packet_timer[i] != 0 ) and (time_after_send > time_out):
                    msg = msg_preprocess(i)
                    logger("{:.3f} pkt: {}\t| timeout since {:.3f}\n".format(now, i, packet_timer[i]), log_name)
                    logger("{:.3f} pkt: {}\t| retransmitted\n".format(now, i), log_name)
                    send_socket.sendto(msg + packet[i], receiver_addr) 
                    packet_timer[i] = now     
        if done:
            return
        
def recv_ack(file_name, packet_num, receiver_addr, window_size):
    global packet, packet_timer, done, nextseqnum, base, ack, log_name

    while True:
        with threading.Lock():
            msg, receiver_addr = send_socket.recvfrom(4096)
            now = time.time()-start_t
            header = msg[:6].decode()
            ack = int(header.split("|")[0])
            logger("{:.3f} ACK: {}\t| received\n".format(now, ack), log_name)

            if base == ack:
                packet_timer[ack] = 0

            if ack+1 == packet_num:
                msg = "2|"
                send_socket.sendto(msg.encode(), receiver_addr)
                done = True
                now = time.time() - start_t
                logger('\n', log_name)
                logger("File transfer is finished\n", log_name)
                logger("Throughput: {:.2f} pkts / sec\n".format(packet_num/now), log_name)
                return

            if base <= ack:
                diff = ack - base
                for i in range(diff+1):
                    packet_timer[base] = 0
                    base +=1
                dup_cnt = 0
            
            elif ack < base:
                dup_cnt += 1
                if dup_cnt == 3:
                    msg = msg_preprocess(ack+1)
                    logger("{:.3f} pkt: {}\t| 3 duplicated ACKs\n".format(now, ack), log_name)
                    logger("{:.3f} pkt: {}\t| retransmitted\n".format(now, ack+1), log_name)
                    send_socket.sendto(msg + packet[ack+1], receiver_addr) 
                    packet_timer[ack+1] = now
                    

        
                        

def main():
    global packet, packet_timer, start_t, done, nextseqnum, base, log_name
    
    receiver_host = input("Receiver IP address : ")
    window_size = int(input("widnow size: "))
    time_out = float(input("timeout (sec): "))
    print()
    file_name  = input("file_name: ")
    receiver_port = 10080
    receiver_addr = (receiver_host, receiver_port) 

    

    with open(file_name, 'rb') as f:
        while True:
            data = f.read(packet_size)
            if not data:
                break
            packet.append(data)

    packet_num = len(packet)
    packet_timer = [0] * packet_num
    start_t = time.time()
    msg = "0|" + file_name + "|" + str(packet_num) + "|" + str(start_t)
    send_socket.sendto(msg.encode(), receiver_addr)

    log_name = file_name + '_sending_log.txt'
    flog = open(log_name, 'w+')
    send_thread = threading.Thread(target = send_packet, args = (file_name, packet_num, receiver_addr, window_size, time_out))
    recv_thread = threading.Thread(target = recv_ack, args = (file_name, packet_num, receiver_addr, window_size))
    
    send_thread.start()
    recv_thread.start()
    send_thread.join()
    recv_thread.join()
    
    send_socket.close()

if __name__ == '__main__':
    main()