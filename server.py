import socket
import threading
import cv2
import pickle
import struct
import imutils

def video_send_frames(video_client_socket):
    while True:
        if video_client_socket:
            vid = cv2.VideoCapture("./test_video.mp4")
            while(vid.isOpened()):
                img,frame = vid.read()
                a = pickle.dumps(frame)
                message = struct.pack("Q",len(a))+a
                video_client_socket.sendall(message)
                cv2.imshow("Client_Client",frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    video_client_socket.close()
                    cv2.destroyAllWindows()
                    break
def video_rev_frames(video_client_socket):
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
        cv2.imshow("Client_Server",frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            video_client_socket.close()
            cv2.destroyAllWindows()
            break



video_server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
video_host_name  = socket.gethostname()
video_host_ip = socket.gethostbyname(video_host_name)
print('HOST IP:',video_host_ip)
video_port = 10050


socket_address = (video_host_ip,video_port)
print('Socket created')
video_server_socket.bind(socket_address)
print('Socket bind complete')
video_server_socket.listen(5)
print('Socket now listening')


try:
    video_client_socket,video_addr = video_server_socket.accept()
    print('Connection from:',video_addr)
    video_send_thread = threading.Thread(target=video_send_frames, args=(video_client_socket,))
    video_send_thread.start()
    video_rev_thread = threading.Thread(target=video_rev_frames, args=(video_client_socket,))
    video_rev_thread.start()
    
except KeyboardInterrupt:
    print("서버 종료")
    video_server_socket.close()
    exit()

