import os
import datetime
import socket
import threading

error_message = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <title>Error response</title>
    </head>
    <body>
        <h1>Error response</h1>
        <p>Error code: {code:}</p>
        <p>Error code explanation: {code:} - {detail:} - {explain}.</p>
    </body>
</html>
"""


def msg_parser(msg, data):
    if(data == 'exp'):
        exp_time_idx = msg.find('expired=')
        exp_time = msg[exp_time_idx+8:].split('\r\n')[0]
        exp_time = exp_time.split(';')[0].strip()
        return exp_time
    if(data == 'id'):
        user_id_idx = msg.find('id=')+3
        if(user_id_idx == 2):
            return -1
        user_id_fin = msg.find('&password=')
        user_id = msg[user_id_idx:user_id_fin]
        return user_id
    if(data == 'cd'):
        user_id_idx = msg.find('cd=')
        if(user_id_idx == -1):
            return -1
        user_id = msg[user_id_idx:].split('=')[1].split(";")[0]
        return user_id

def is_expired(exp_time):
    if(exp_time == 0):
        return -1
    now = datetime.datetime.now()
    cur = now.minute*60 + now.second      
    exp = 30 - (cur - int(exp_time))
    return exp

def send_data (connSock, header, is_bytedata = True, data = None):
    try :
        if data == None:
            response = header.encode()
        else:
            if is_bytedata == True:
                response = header.encode() + data
            else:
                response = (header + data).encode()
        header_list = header.split('\r\n')
        print('[response: ', end=' ')
        for i in header_list:
            if i != '':
                print(i, end =' ')
        print(']')
        connSock.sendall(response)
        
    except socket.error:
        print("Sending Error")

def send_error(conn, code, explain):
    
    if code == 403:
        content = error_message.format(code = code, detail = 'Forbidden',explain = explain)
        data = content.encode('UTF-8')
        header = 'HTTP/1.1 403 Forbidden\r\nSet-Cookie:cd={}\r\nSet-Cookie:expired=0\r\n\r\n'.format(None)
    elif code == 404:
        content = error_message.format(code = code, detail = 'Not Found',explain = explain)
        data = content.encode('UTF-8')
        header = 'HTTP/1.1 404 Not Found\r\nContent-Length: {}\r\n\r\n'.format(len(data))         
    send_data(conn, header, True, data) 
     

def req_handler(connection_socket):
    msg = connection_socket.recv(1024).decode()
    request = msg.split(' ')
    req_method = request[0]
    print("[method : ", req_method, ']')
    try:
        if(req_method == 'GET'):
            file_name = request[1]
            if(file_name == '/'):
                send_data(connection_socket, 'HTTP/1.1 302 FOUND\r\nLocation:/index.html\r\n\r\n')
            if(file_name == '/index.html'):
                f = open(file_name[1:], "rb")
                print("[FILE OPENED] : ", file_name)
                data = f.read()
                header = ('HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type:text/html\r\n\r\n').format(len(data))
                send_data(connection_socket, header, True, data)    
            elif(file_name == '/cookie.html'):
                user_id = msg_parser(msg, 'cd')
                if(user_id == -1):
                    send_error(connection_socket, 403, 'User not found')
                exp_time = msg_parser(msg, 'exp')
                exp = is_expired(exp_time)
                print("[EXP] : ", exp)
                if(exp <= 0):
                    send_error(connection_socket, 403, 'you are logged out')
                else:              
                    f = open(file_name[1:])
                    print("[FILE OPENED] : ", file_name)
                    data = f.read().format(user_id = user_id, time = exp).encode()
                    header = ('HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type:text/html\r\n\r\n').format(len(data))
                    send_data(connection_socket, header, True, data)
            
            elif(file_name == '/favicon.ico'):
                pass
            
            elif(file_name == '/secret.html'):
                user_id = msg_parser(msg, 'cd')
                if(user_id == -1):
                    send_error(connection_socket, 403, 'User not found')
                exp_time = msg_parser(msg, 'exp')
                exp = is_expired(exp_time)
                print("[EXP] : ", exp)
                if(exp <= 0):
                    send_error(connection_socket, 403, 'you are logged out')
                else:
                    f = open(file_name[1:], "rb")
                    print("[FILE OPENED] : ", file_name)
                    data = f.read()
                    header = ('HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type:text/html\r\n\r\n').format(len(data))
                    send_data(connection_socket, header, True, data)
            else:
                f = open(file_name[1: ], "rb")
                user_id = msg_parser(msg, 'cd')
                if(user_id == -1):
                    send_error(connection_socket, 403, 'User not found')
                exp_time = msg_parser(msg, 'exp')
                exp = is_expired(exp_time)
                if(exp<=0):
                    send_error(connection_socket, 403, 'you are logged out')
                else:
                    extension = file_name[file_name.rfind(".")+1:]
                    if extension == "jpeg":
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:image/jpeg\r\n\r\n')
                    elif extension == "html":
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n')
                    elif extension == "mp4":
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:video/mp4\r\n\r\n')
                    elif extension == "pdf":
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:application/pdf\r\n\r\n')
                    else:
                        header = ('HTTP/1.1 200 OK\r\nContent-Type:application/octet-stream\r\n\r\n')
                    send_data(connection_socket, header)
                    while(True):
                        data = f.read(1024)
                        if not data:
                            break
                        connection_socket.sendall(data)

        elif(req_method == 'POST'):
            file_name = request[1]
            if(file_name == '/index.html'):
                user_id =  msg_parser(msg, 'id')
                if(user_id == -1):
                    send_error(connection_socket, 403, 'User not found')
                print("[User_ID] : ", user_id)
                header = 'HTTP/1.1 302 FOUND\r\nLocation:/secret.html\r\nContent-Type:text/html\r\nSet-Cookie:cd={}\r\n'.format(user_id)
                now = datetime.datetime.now()
                cur = now.minute*60 + now.second
                header += 'Set-Cookie:expired={}\r\n\r\n'.format(cur) 
            send_data(connection_socket, header)
            
    
    except FileNotFoundError:
        send_error(connection_socket, 404, 'File not found')

def my_server():
    server_host, server_port = '', 10080
    address = (server_host, server_port)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(address)
    server_socket.listen(200)
    print('The server is ready to receive.')

    try:
        while True:
            connection_socket, client_addr = server_socket.accept()
            print('Connected to : ', client_addr[0], ':', client_addr[1])
            my_thread = threading.Thread(
                target=req_handler, args=(connection_socket,))
            my_thread.start()
    
    except KeyboardInterrupt:
        server_socket.close()


if __name__ == '__main__':
    my_server()  
