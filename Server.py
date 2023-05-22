import socket
import threading
import cv2
import pickle
import struct
import imutils




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

class UserManager:  
    # 사용자관리 및 채팅 메세지 전송을 담당하는 클래스
    # ① 채팅 서버로 입장한 사용자의 등록
    # ② 채팅을 종료하는 사용자의 퇴장 관리
    # ③ 사용자가 입장하고 퇴장하는 관리
    # ④ 사용자가 입력한 메세지를 채팅 서버에 접속한 모두에게 전송

    def __init__(self):
        self.users = {}  # 사용자의 등록 정보를 담을 사전 {사용자 이름:(소켓,주소),...}

    def addUser(self, username, conn, addr):  # 사용자 ID를 self.users에 추가하는 함수
        if username in self.users:  # 이미 등록된 사용자라면
            conn.send('이미 등록된 사용자입니다.\n'.encode())
            return None

        # 새로운 사용자를 등록함
        lock.acquire()  # 스레드 동기화를 막기위한 락
        self.users[username] = (conn, addr)
        lock.release()  # 업데이트 후 락 해제

        self.sendMessageToAll('[%s] 님이 입장했습니다.' % username)
        print('+ 채팅 참여자 수 [%d]' % len(self.users))

        return username

    def removeUser(self, username):  # 사용자를 제거하는 함수
        if username not in self.users:
            return

        lock.acquire()
        del self.users[username]
        lock.release()

        self.sendMessageToAll('[%s]님이 퇴장했습니다.' % username)
        print('- 대화 참여자 수 [%d]' % len(self.users))

    def messageHandler(self, username, msg):  # 전송한 msg를 처리하는 부분
        if msg[0] != '/':  # 보낸 메세지의 첫문자가 '/'가 아니면
            self.sendMessageToAll('[%s] %s' % (username, msg))
            return

        if msg.strip() == '/end':  # 보낸 메세지가 'end'이면
            self.removeUser(username)
            return -1

    def sendMessageToAll(self, msg):
        for conn, addr in self.users.values():
            conn.send(msg.encode())


class MyTcpHandler(socketserver.BaseRequestHandler):
    userman = UserManager()

    def handle(self):  # 클라이언트가 접속시 클라이언트 주소 출력
        print('[%s] 연결됨' % self.client_address[0])

        try:
            username = self.registerUsername()
            msg = self.request.recv(1024)
            while msg:
                print(msg.decode())
                if self.userman.messageHandler(username, msg.decode()) == -1:
                    self.request.close()
                    break
                msg = self.request.recv(1024)

        except Exception as e:
            print(e)

        print('[%s] 접속종료' % self.client_address[0])
        self.userman.removeUser(username)

    def registerUsername(self):
        while True:
            self.request.send('로그인ID:'.encode())
            username = self.request.recv(1024)
            username = username.decode().strip()
            if self.userman.addUser(username, self.request, self.client_address):
                return username


class ChatingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def runServer():
    print('server start')

    try:
        server = ChatingServer((HOST, PORT), MyTcpHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('server end')
        server.shutdown()
        server.server_close()

# 클라이언트와의 연결을 관리하는 함수
async def handle_client(websocket, path):
    async for message in websocket:
        data = json.loads(message)

        # 화면 스크린샷 요청 처리
        if data["type"] == "request_screen":
            screenshot = pyautogui.screenshot()
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            screenshot_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            # 클라이언트에게 스크린샷 전송
            await websocket.send(json.dumps({"type": "screen", "data": screenshot_base64}))

        # 마우스 클릭 요청 처리
        elif data["type"] in ["mouse_down", "mouse_up"]:
            x, y, button = data["data"]
            if data["type"] == "mouse_down":
                pyautogui.mouseDown(x, y, button=button)
            else:
                pyautogui.mouseUp(x, y, button=button)

        # 키보드 입력 요청 처리
        elif data["type"] == "write":
            text = data["text"]
            pyautogui.write(text)


        # 마우스 드래그
        elif data["type"] == "drag":
            x1, y1, x2, y2, button = data["data"]
            pyautogui.moveTo(x1, y1)
            pyautogui.dragTo(x2, y2, button=button)

        # 마우스 누르기
        elif data["type"] == "mouse_down":
            x, y, button = data["data"]
            pyautogui.mouseDown(x, y, button=button)

        # 마우스 떼기
        elif data["type"] == "mouse_up":
            x, y, button = data["data"]
            pyautogui.mouseUp(x, y, button=button)


# SFTP 서버 구성을 위한 클래스 정의
class SFTPServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        # 인증 로직 구현
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        # 채널 요청 검증
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        # 허용되는 인증 방법 구현
        return 'password'

    def check_channel_exec_request(self, channel, command):
        # 명령어 실행 요청 검증
        return True

def SFTP_func :
    # SFTP 클라이언트 연결 대기
    channel = sftpserver.accept(20)
    if channel is None:
        print("SFTP client connection failed")
        sftpserver.close()
        sys.exit(1)

    # 파일 업로드 처리
    sftp = channel.makefile("rU")
    sftp.write("SFTP server ready.\n")
    sftp.flush()

    while True:
        header = sftp.readline()
        if header.startswith("C"):
            parts = header.split()
            size = int(parts[1])
            filename = parts[2]
            print(f"Uploading file {filename} ({size} bytes)")
            data = sftp.read(size)
            print(data)
        else:
            break



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

# # SFTP 서버 설정
# host_key = paramiko.RSAKey.generate(2048)
# sftpserver = paramiko.Transport(('127.0.0.1', 22))
# sftpserver.add_server_key(host_key)
# server = SFTPServer()
# # SFTP 서버 실행
# try:
#     sftpserver.start_server(server=server)
# except Exception as e:
#     print(f"Error: {str(e)}")

HOST = ''
PORT = 9020
lock = threading.Lock() 


try:
    # chat server
    runServer()

    # 웹소켓 서버 시작 // screen server
    start_server = websockets.serve(handle_client, "0.0.0.0", 8765)
    # 이벤트 루프 실행
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

    # SFTP_thread = threading.Thread(target=SFTP_func, args=())
    video_client_socket,video_addr = video_server_socket.accept()
    print('Connection from:',video_addr)
    video_client_sockets.append(video_client_socket)
    print('connected client count : ', len(video_client_sockets))
    video_client_thread = threading.Thread(target=video_handle_client, args=(video_client_socket, video_client_sockets, ))
    video_client_thread.start()
except KeyboardInterrupt:
    print("서버 종료")
    sftp.close()
    channel.close()
    sftpserver.close()
    video_server_socket.close()
    exit()


