import cv2

# 웹캠 열기
cap = cv2.VideoCapture(0)

while True:
    # 비디오 프레임 읽기
    ret, frame = cap.read()

    # 프레임 표시
    cv2.imshow('Webcam', frame)

    # q를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 리소스 해제
cap.release()
cv2.destroyAllWindows()