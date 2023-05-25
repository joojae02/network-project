import asyncio
import websockets
import pyautogui
import json
import base64
import io

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
        
class SFTPServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        # 사용자 이름과 비밀번호가 일치하는지 확인
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        # 클라이언트로부터 채널 요청이 왔을 때의 동작 정의
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        # 허용되는 인증 방법을 반환
        return 'password'

    def check_channel_exec_request(self, channel, command):
        # 채널 실행 요청을 확인
        return True

class SFTPServerUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SFTP Server")

        # 클라이언트의 SFTP 서버에 연결하여 SFTP 클라이언트 생성
        client_hostname = "192.168.0.0"  # 클라이언트 IP 주소
        client_port = 22  # 클라이언트 포트 번호
        client_username = "username"  
        client_password = "password"  

        # 클라이언트 호스트와 포트로 트랜스포트 객체 생성 및 연결
        self.client_transport = paramiko.Transport((client_hostname, client_port))
        self.client_transport.connect(username=client_username, password=client_password)
        # 트랜스포트를 사용해 SFTP 클라이언트 생성
        self.client_sftp = paramiko.SFTPClient.from_transport(self.client_transport)

        # GUI 생성 - 파일 업로드 버튼 및 종료 버튼 추가
        self.upload_button = tk.Button(self, text="Select File to Upload", command=self.sftp_upload)
        self.upload_button.pack()
        self.quit_button = tk.Button(self, text="QUIT", fg="red", command=self.on_closing)
        self.quit_button.pack()

    def sftp_upload(self):
        # 파일 다이얼로그를 통해 업로드할 파일 선택
        filepath = filedialog.askopenfilename()
        if filepath:
            # 선택된 파일의 이름을 가져와서 원격 경로 생성
            filename = filepath.split("/")[-1]
            remote_file_path = f'/tmp/{filename}'
            # 선택된 파일을 원격 경로로 업로드
            self.client_sftp.put(filepath, remote_file_path)
            print(f"파일 {filename}이(가) 클라이언트에 성공적으로 업로드되었습니다.")

    def on_closing(self):
        # 프로그램 종료시 SFTP 클라이언트 및 트랜스포트를 닫고 GUI를 파괴
        self.client_sftp.close()
        self.client_transport.close()
        self.destroy()


def start_sftp_server():
    # RSA 키를 생성하고 SFTP 서버를 설정
    host_key = paramiko.RSAKey.generate(2048)
    sftpserver = paramiko.Transport(('localhost', 22))
    sftpserver.add_server_key(host_key)
    server = SFTPServer()

    # 서버를 시작
    try:
        sftpserver.start_server(server=server)
    except Exception as e:
        print(f"에러: {str(e)}")


class ChatServer(tk.Tk):
    def __init__(self, loop):
        super().__init__()
        self.title("Server")
        self.loop = loop
        self.websocket = None

        self.chat_box = tk.Text(self, state='disabled')
        self.chat_box.pack()

        self.msg_entry = tk.Entry(self)
        self.msg_entry.bind("<Return>", self.on_entry_return)
        self.msg_entry.pack()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    async def start_server(self):
        self.websocket = await websockets.serve(self.server, 'localhost', 8765)

    async def server(self, websocket, path):
        connected.add(websocket)
        try:
            while True:
                message = await websocket.recv()
                print(f"Other: {message}")  # 받은 내용을 출력
                self.chat_box.configure(state='normal')
                self.chat_box.insert('end', f"Other: {message}\n")
                self.chat_box.configure(state='disabled')

                # 에코 서버 예제
                # for conn in connected:
                #     await conn.send(message)  # 받은 내용을 연결된 모든 클라이언트로 전송
                #     print(f"보낸 내용: {message}")  # 보낸 내용을 출력
                #     self.chat_box.configure(state='normal')
                #     self.chat_box.insert('end', f"보낸 내용: {message}\n")
                #     self.chat_box.configure(state='disabled')

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            connected.remove(websocket)

    def on_entry_return(self, event):
        msg = self.msg_entry.get()
        self.msg_entry.delete(0, 'end')

        for conn in connected:
            self.loop.create_task(conn.send(msg))
            print(f"Me: {msg}")  # 서버에서 클라이언트로 보낸 메시지를 출력
            self.chat_box.configure(state='normal')
            self.chat_box.insert('end', f"Me: {msg}\n")
            self.chat_box.configure(state='disabled')

    def on_closing(self):
        for conn in connected:
            self.loop.create_task(conn.close())

        self.destroy()  


# 별도의 쓰레드에서 SFTP 서버를 시작
server_thread = threading.Thread(target=start_sftp_server)
server_thread.start()

# 메인 쓰레드에서 GUI를 실행
server_ui = SFTPServerUI()
server_ui.protocol("WM_DELETE_WINDOW", server_ui.on_closing)
server_ui.mainloop()

# GUI가 종료되면 서버 쓰레드를 종료
server_thread.join()

# 웹소켓 서버 시작
start_server = websockets.serve(handle_client, "0.0.0.0", 8765)

# 이벤트 루프 실행
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


connected = set()

loop = asyncio.get_event_loop()
chat_server = ChatServer(loop)

loop.run_until_complete(chat_server.start_server())

def run_tk():
    chat_server.update()
    loop.call_later(0.05, run_tk)

run_tk()
loop.run_forever()