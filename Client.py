import socket
import threading
import cv2
import pickle
import struct
import imutils


def video_send_frames():
    while True:
        if video_client_socket:
            vid = cv2.VideoCapture(0)
            while(vid.isOpened()):
                img,frame = vid.read()
                a = pickle.dumps(frame)
                message = struct.pack("Q",len(a))+a
                video_client_socket.sendall(message)
                key = cv2.waitKey(10) 
                if key ==13:
                    video_client_socket.close()
def video_rev_frames():
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
        cv2.imshow("Client1",frame)
        key = cv2.waitKey(10) 
        if key  == 13:
            break


class ChatWindow:
    def __init__(self, master):
        self.master = master
        master.title("Chat Client")

        self.chat_log = tk.Text(master)
        self.chat_log.pack()

        self.input_label = tk.Label(master, text="Enter your message:")
        self.input_label.pack()

        self.input_field = tk.Entry(master, font=("Helvetica", 16))
        self.input_field.pack()
        self.input_field.bind("<Return>", self.send_msg)

        self.send_button = tk.Button(
            master, text="Send", command=self.send_msg)
        self.send_button.pack()

        self.quit_button = tk.Button(
            master, text="Quit", command=self.quit_chat)
        self.quit_button.pack()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))

        self.receive_thread = threading.Thread(target=self.receive_msgs)
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def send_msg(self, event=None):
        msg = self.input_field.get()
        self.input_field.delete(0, tk.END)
        self.sock.send(msg.encode())

    def update_chat_log(self, data):
        self.chat_log.insert(tk.END, data + "\n")

    def receive_msgs(self):
        while True:
            data = self.sock.recv(1024)
            if not data:
                break
            self.master.after(0, self.update_chat_log, data.decode())

    def quit_chat(self):
        self.sock.send('/end'.encode())
        self.sock.close()
        self.master.destroy()


def start_client():
    root = tk.Tk()
    chat_window = ChatWindow(root)
    root.mainloop()


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

HOST = 'localhost'
PORT = 9020

ADDR="ws://192.1.1.1:8765"

video_client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
video_host_ip = '172.30.1.24'
video_port = 10050 


try:
    video_client_socket.connect((video_host_ip,video_port)) 
    start_client()
    print('서버에 연결되었습니다.')

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    root = tk.Tk()  # 루트 윈도우 생성
    canvas = tk.Canvas(root, width=1440, height=900)  # 캔버스 생성
    canvas.pack()
    threading.Thread(target=asyncio.run, args=(run_main(root, canvas),), daemon=True).start()
    root.mainloop()

    video_send_thread = threading.Thread(target=video_send_frames)
    video_send_thread.start()
    video_rev_thread = threading.Thread(target=video_rev_frames)
    video_rev_thread.start()

except KeyboardInterrupt:
    print("서버 종료")
    video_client_socket.close()
    exit()
