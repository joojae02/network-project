import time
import cv2
import socket
import struct
import pickle
import threading

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
            # cv2.imshow('Webcam', frame)

            # # q를 누르면 종료
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
            # 프레임을 직렬화
            data = pickle.dumps(frame)

            # 직렬화된 데이터의 크기 전송
            message = struct.pack("L", len(data))+ data
            client_socket.sendall(message)

    except Exception as e:
        print('비디오 프레임 전송 중 에러:', e)

def receive_frames():
    try:
        while True:
            # 서버로부터 받은 프레임 수신
            received_data = b""
            message_size_data = client_socket.recv(8)
            if message_size_data == True :
                if len(message_size_data) == 8:
                    message_size = struct.unpack("L", message_size_data)[0]
                    while len(received_data) < message_size:
                        data_chunk = client_socket.recv(8)
                        if not data_chunk:
                            break
                        received_data += data_chunk

                    # 수신한 프레임 역직렬화
                    if len(received_data) == message_size:
                        frame_data = received_data[struct.calcsize("L"):]
                        received_frame = pickle.loads(frame_data)

                        # 받은 프레임 표시
                        cv2.imshow('Received Frame A', received_frame)
            else :
                print("수신 받은 데이터가 없습니다")
                print('재연결까지 3초 대기...')
                time.sleep(3)



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
