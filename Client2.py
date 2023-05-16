import socket
import threading
import cv2
import pickle
import struct
import imutils

client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host_ip = '172.30.1.24'# Standard loopback interface address (localhost)
port = 10050 # Port to listen on (non-privileged ports are > 1023)

def send_frames():
    while True:
        if client_socket:
            vid = cv2.VideoCapture(0)
            while(vid.isOpened()):
                img,frame = vid.read()
                a = pickle.dumps(frame)
                message = struct.pack("Q",len(a))+a
                client_socket.sendall(message)
                key = cv2.waitKey(10) 
                if key ==13:
                    client_socket.close()
def rev_frames():
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
        cv2.imshow("Client2",frame)
        key = cv2.waitKey(10) 
        if key  == 13:
            break

try:
    client_socket.connect((host_ip,port)) 
    print('서버에 연결되었습니다.')
    send_thread = threading.Thread(target=send_frames)
    send_thread.start()
    rev_thread = threading.Thread(target=rev_frames)
    rev_thread.start()

except KeyboardInterrupt:
    print("서버 종료")
    client_socket.close()
    exit()
