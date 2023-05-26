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
                #cv2.imshow("Client_Client",frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    video_client_socket.close()
                    cv2.destroyAllWindows()
                    break
        vid.release()


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
        cv2.imshow("Client_Server", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            video_client_socket.close()
            cv2.destroyAllWindows()
            break




video_client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
video_host_ip = '192.168.77.129'
video_port = 10050

try:
    video_client_socket.connect((video_host_ip,video_port)) 
    print('서버에 연결되었습니다.')
    video_send_thread = threading.Thread(target=video_send_frames, args=(video_client_socket,))
    video_send_thread.start()
    video_rev_thread = threading.Thread(target=video_rev_frames, args=(video_client_socket, ))
    video_rev_thread.start()

except KeyboardInterrupt:
    print("서버 종료")
    video_client_socket.close()
    exit()

