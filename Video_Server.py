import socket
import threading
import cv2
import pickle
import struct
import imutils

video_server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
video_host_name  = socket.gethostname()
video_host_ip = socket.gethostbyname(video_host_name)
print('HOST IP:',video_host_ip)
video_port = 10050
video_client_sockets = []

socket_address = (video_host_ip,video_port)
print('Socket created')
video_server_socket.bind(socket_address)
print('Socket bind complete')
video_server_socket.listen(5)
print('Socket now listening')

def video_handle_client(video_client_socket, video_client_sockets):
    try :
        data = b""
        payload_size = struct.calcsize("Q")
        while True :
            while len(data) < payload_size:
                packet = video_client_socket.recv(4*1024)
                if not packet: break
                data+=packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q",packed_msg_size)[0]
            while len(data) < msg_size:
                data += video_client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data  = data[msg_size:]
            frame = pickle.loads(frame_data)
            a = pickle.dumps(frame)
            message = struct.pack("Q",len(a))+a
            send_to_clients(message, video_client_socket, video_client_sockets)    
            key = cv2.waitKey(10) 
            if key  == 13:
                break
    except Exception as e :
        print("클라이언트 종료: ", video_client_socket.getpeername())
        video_client_socket.close()

def send_to_clients(message, sender_socket, video_client_sockets):
    for video_client_socket in video_client_sockets :
        if video_client_socket is not sender_socket :
            video_client_socket.sendall(message)
try:
    while True:
        video_client_socket,video_addr = video_server_socket.accept()
        print('Connection from:',video_addr)
        video_client_sockets.append(video_client_socket)
        print('connected client count : ', len(video_client_sockets))
        video_client_thread = threading.Thread(target=video_handle_client, args=(video_client_socket, video_client_sockets, ))
        video_client_thread.start()
except KeyboardInterrupt:
    print("서버 종료")
    video_server_socket.close()
    exit()


