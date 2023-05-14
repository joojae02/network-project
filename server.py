import cv2
import socket
import struct
import pickle
import threading

def handle_client(client_socket):
    try:
        print('클라이언트 연결:', client_socket.getpeername())
        while True:
            msg_size, data = receive_data(client_socket)
            print("data length : ", len(data))
            # send_data_to_other_clients(data, client_socket)

    except Exception as e:
        print('에러 발생:', e)

    finally:
        print("클라이언트 종료: ", client_socket.getpeername())
        client_socket.close()

def receive_data(client_socket):
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
    return  msg_size, data

def send_data_to_other_clients(data, sender_socket):
    # 모든 클라이언트에게 데이터 전송
    for client_socket in client_sockets:
        if client_socket is not sender_socket:
            try:
                message = struct.pack("Q", len(data))+ data
                # 데이터 전송
                client_socket.sendall(message)

            except Exception as e:
                print('에러 발생:', e)


# 서버 소켓 생성
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print("Host IP:", host_ip)
port = 9999
socket_address = (host_ip, port)

# 서버 소켓 바인딩
server_socket.bind(socket_address)

# 클라이언트 소켓 리스트
client_sockets = []

# 클라이언트 연결 대기
server_socket.listen(2)
print("서버 대기 중...")

try:
    while True:
        # 클라이언트 연결 수락
        client_socket, addr = server_socket.accept()
        print('클라이언트 연결:', addr)
        # 클라이언트 소켓 저장
        client_sockets.append(client_socket)
        print('연결된 클라이언트 수 : ', len(client_sockets))

        # 클라이언트 핸들링을 위한 스레드 생성
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

except KeyboardInterrupt:
    print("서버 종료")

finally:
    # 리소스 해제
    server_socket.close()
