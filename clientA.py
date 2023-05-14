import time
import cv2
import socket
import struct
import pickle
import threading
import imutils

# 웹캠 설정
cap = cv2.VideoCapture(0)

# 서버 주소 및 포트
server_ip = '172.30.1.16'
server_port = 9999

# 서버 소켓 생성
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send_frames():
    try:
        while True:
            # 비디오 프레임 읽기
            ret, frame = cap.read()
            # 프레임을 직렬화
            data = pickle.dumps(frame)

            # 직렬화된 데이터의 크기 전송
            message = struct.pack("Q", len(data))+ data
            print("size :", len(message))
            client_socket.sendall(message)

    except Exception as e:
        print('비디오 프레임 전송 중 에러:', e)

def receive_frames():
    try:
        while True:
            # 서버로부터 받은 프레임 수신
            data = b""
            payload_size = struct.calcsize("Q")
            print("payload_size :", payload_size)
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024) # 4K
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
            cv2.imshow("Receiving...",frame)
            cv2.imshow("CLIENT A",frame)



    except Exception as e:
        print('프레임 수신 중 에러:', e)


def reconnect():
    while True:
        try:
            print('서버와 재연결 시도...')
            client_socket.connect((server_ip, server_port))
            print('서버에 연결되었습니다.')
            break
        except socket.error as e:
            print('서버 연결 에러:', e)
            print('재연결까지 3초 대기...')
            time.sleep(3)

try:
    # 서버에 연결
    client_socket.connect((server_ip, server_port))
    print('서버에 연결되었습니다.')

    # 비디오 프레임 전송 스레드 시작
    send_thread = threading.Thread(target=send_frames)
    send_thread.start()

    # 프레임 수신 스레드 시작
    # receive_thread = threading.Thread(target=receive_frames)
    # receive_thread.start()

    # 메인 스레드에서 키 입력 대기
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except socket.error as e:
    print('서버 연결 에러:', e)

finally:
    # 리소스 해제
    cap.release()
    cv2.destroyAllWindows()
    client_socket.close()
