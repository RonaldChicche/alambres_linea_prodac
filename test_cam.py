# script para leer camara con opnecv y mostrar
import cv2
import numpy as np
import base64
import time

cap = cv2.VideoCapture(0)
cap1 = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (640, 480))
        frame = cv2.flip(frame, 1)
        frame_base64 = base64.b64encode(frame).decode('utf-8')
        cv2.imshow('frame', frame)

    ret1, frame1 = cap1.read()
    if ret1:
        frame1 = cv2.resize(frame1, (640, 480))
        frame1 = cv2.flip(frame1, 1)
        frame_base64_1 = base64.b64encode(frame1).decode('utf-8')
        cv2.imshow('frame1', frame1)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    time.sleep(0.1) 

cap.release()
cv2.destroyAllWindows()