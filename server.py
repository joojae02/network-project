import socket
import threading
import cv2
import pickle
import struct
import imutils

server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host_name  = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP:',host_ip)
port = 10050
client_sockets = []

socket_address = (host_ip,port)
print('Socket created')
server_socket.bind(socket_address)
print('Socket bind complete')
server_socket.listen(5)
print('Socket now listening')

def handle_client(client_socket, client_sockets):
    try :
        data = b""
        payload_size = struct.calcsize("Q")
        while True :
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024)
                if not packet: break
                data+=packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q",packed_msg_size)[0]
            while len(data) < msg_size:
                data += client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data  = data[msg_size:]
            frame = pickle.loads(frame_data)
            a = pickle.dumps(frame)
            message = struct.pack("Q",len(a))+a
            send_to_clients(message, client_socket, client_sockets)    
            key = cv2.waitKey(10) 
            if key  == 13:
                break
    except Exception as e :
        print("클라이언트 종료: ", client_socket.getpeername())
        client_socket.close()

def send_to_clients(message, sender_socket, client_sockets):
    for client_socket in client_sockets :
        if client_socket is not sender_socket :
            client_socket.sendall(message)
try:
    while True:
        client_socket,addr = server_socket.accept()
        print('Connection from:',addr)
        client_sockets.append(client_socket)
        print('connected client count : ', len(client_sockets))
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_sockets, ))
        client_thread.start()
except KeyboardInterrupt:
    print("서버 종료")
    server_socket.close()
    exit()


