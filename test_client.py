import base64
import io
import json
import tkinter as tk
from PIL import Image, ImageTk
import websockets
import asyncio
import paramiko
from tkinter import filedialog
import aiohttp
from aiohttp import web
import socket
import threading
import cv2
import pickle
import struct
import imutils


# 서버에게 스크린샷을 요청하는 함수
async def request_screenshot(websocket):
    await websocket.send(json.dumps({"type": "request_screen"}))
    response = await websocket.recv()
    data = json.loads(response)
    if data["type"] == "screen":
        screenshot_base64 = data["data"]
        return Image.open(io.BytesIO(base64.b64decode(screenshot_base64)))

# 화면 갱신을 위한 함수
async def update_screen(websocket, canvas):
    while True:
        screenshot = await request_screenshot(websocket)
        tk_image = ImageTk.PhotoImage(screenshot)
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
        canvas.image = tk_image
        canvas.update()

# 메인 함수. 마우스 클릭 이벤트와 키보드 입력 이벤트를 처리
async def main(websocket, root, canvas):
    loop = asyncio.get_event_loop()

    start = None

    # 드래그 시작 이벤트 처리 함수
    def on_mouse_down(event):
        nonlocal start
        start = (event.x, event.y)
        data = {"type": "mouse_down", "data": [start[0], start[1], "left"]}
        loop.call_soon_threadsafe(lambda: asyncio.create_task(websocket.send(json.dumps(data))))

    # 드래그 종료 이벤트 처리 함수
    def on_mouse_up(event):
        nonlocal start
        if start is not None:
            data = {"type": "mouse_up", "data": [event.x, event.y, "left"]}
            loop.call_soon_threadsafe(lambda: asyncio.create_task(websocket.send(json.dumps(data))))
            start = None

    # 오른쪽 마우스 버튼 누름 이벤트 처리 함수
    def on_right_mouse_down(event):
        data = {"type": "mouse_down", "data": [event.x, event.y, "right"]}
        loop.call_soon_threadsafe(lambda: asyncio.create_task(websocket.send(json.dumps(data))))

    # 오른쪽 마우스 버튼 놓음 이벤트 처리 함수
    def on_right_mouse_up(event):
        data = {"type": "mouse_up", "data": [event.x, event.y, "right"]}
        loop.call_soon_threadsafe(lambda: asyncio.create_task(websocket.send(json.dumps(data))))

    # 키보드 입력 이벤트 처리 함수
    def on_key_press(event):
        data = {"type": "write", "text": event.char}
        loop.call_soon_threadsafe(lambda: asyncio.create_task(websocket.send(json.dumps(data))))

    canvas.bind("<Button-1>", on_mouse_down)  # 캔버스에 마우스 버튼 누름 이벤트 바인딩
    canvas.bind("<ButtonRelease-1>", on_mouse_up)  # 캔버스에 마우스 버튼 놓음 이벤트 바인딩
    canvas.bind("<Button-3>", on_right_mouse_down)  # 캔버스에 오른쪽 마우스 버튼 누름 이벤트 바인딩
    canvas.bind("<ButtonRelease-3>", on_right_mouse_up)  # 캔버스에 오른쪽 마우스 버튼 놓음 이벤트 바인딩
    root.bind("<Key>", on_key_press)  # 루트 윈도우에 키보드 이벤트 바인딩

    while True:
        await update_screen(websocket, canvas)  # 화면 갱신

# 웹소켓 서버에 연결하고 메인 함수 실행
async def run_main(root, canvas):
    async with websockets.connect(ADDR) as websocket:
        await main(websocket, root, canvas)



class SFTPUploadGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SFTP Upload")
        
        # SFTP 클라이언트 생성 및 연결
        self.transport = paramiko.Transport((hostname, port))
        self.transport.connect(username=username, password=password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        
        # GUI 구성
        self.create_widgets()

    def create_widgets(self):
        self.upload_button = tk.Button(self, text="Select File to Upload", command=self.sftp_upload)
        self.upload_button.pack()

        self.quit_button = tk.Button(self, text="QUIT", fg="red", command=self.close_sftp)
        self.quit_button.pack()

    def sftp_upload(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            filename = filepath.split("/")[-1]  # 파일명 추출
            remote_file_path = f'/tmp/{filename}'  # 변경할 부분: 목적지 경로
            self.sftp.put(filepath, remote_file_path)
            print(f"File {filename} uploaded successfully.")

    def close_sftp(self):
        # SFTP 클라이언트 종료
        self.sftp.close()
        self.transport.close()
        self.quit()



class ChatClient(tk.Tk):
    def __init__(self, loop):
        super().__init__()
        self.title("Client")
        self.loop = loop
        self.websocket = None

        self.chat_box = tk.Text(self, state='disabled')
        self.chat_box.pack()

        self.msg_entry = tk.Entry(self)
        self.msg_entry.bind("<Return>", self.on_entry_return)
        self.msg_entry.pack()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    async def connect(self):
        self.websocket = await websockets.connect('ws://127.0.1.1:8765')

    async def receive_message(self):
        while True:
            msg = await self.websocket.recv()
            self.chat_box.configure(state='normal')
            self.chat_box.insert('end', f"Other: {msg}\n")
            self.chat_box.configure(state='disabled')
            print(f"Other : {msg}")  # 받은 내용을 출력

    def on_entry_return(self, event):
        msg = self.msg_entry.get()
        self.msg_entry.delete(0, 'end')
        self.loop.create_task(self.websocket.send(msg))
        self.chat_box.configure(state='normal')
        self.chat_box.insert('end', f"Me: {msg}\n")
        self.chat_box.configure(state='disabled')
        print(f"Me : {msg}")  # 보낸 내용을 출력

    def on_closing(self):
        self.loop.create_task(self.websocket.close())
        self.destroy()


##################################

def video_send_frames(video_client_socket):
    while True:
        if video_client_socket:
            vid = cv2.VideoCapture("./test_video2.mp4")
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
##################################


# SFTP 서버 정보
hostname = "127.0.1.1"
port = 22
username = "username"
password = "password"

app = SFTPUploadGUI()
app.mainloop()

ADDR="ws://127.0.1.1:8765"
video_client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
video_host_ip = '127.0.1.1'
video_port = 10050

# 기본 이벤트 루프 정책 설정 (tkinter와 호환)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

root = tk.Tk()  # 루트 윈도우 생성
canvas = tk.Canvas(root, width=1440, height=900)  # 캔버스 생성
canvas.pack()

# 별도의 스레드에서 tkinter 이벤트 루프
threading.Thread(target=asyncio.run, args=(run_main(root, canvas),), daemon=True).start()

# tkinter 메인 루프 시작
root.mainloop()

loop = asyncio.get_event_loop()
chat_client = ChatClient(loop)

loop.run_until_complete(chat_client.connect())
loop.create_task(chat_client.receive_message())

def run_tk(root, interval=0.05):  # 50 ms
    def update():
        root.update()
        loop.call_later(interval, update)
    loop.call_soon(update)
    loop.run_forever()

run_tk(chat_client)


try:
    video_client_socket.connect((video_host_ip,video_port)) 
    print('서버에 연결되었습니다.')
    video_send_thread = threading.Thread(target=video_send_frames, args=(video_client_socket,))
    video_send_thread.start()
    video_rev_thread = threading.Thread(target=video_rev_frames, args=(video_client_socket,))
    video_rev_thread.start()

except KeyboardInterrupt:
    print("서버 종료")
    video_client_socket.close()
    exit()

