# script para leer camara con opnecv y mostrar
import cv2
import numpy as np
import base64
import time
from web.ptz_app import PTZCamera

# cam1 = PTZCamera("192.168.90.109", "admin", "Bertek@2060")
cam1 = PTZCamera("192.168.90.108", "admin", "Bertek@206036")

# connect
# cam1.connect()
# cam2.connect()

# start video capture
cam1.start_video_capture()
# cam2.start_video_capture()

while True:
    # read and show cam 1
    frame1 = cam1.video_capture.read()[1]
    # cv2.imshow("cam1", frame1)
    # read and show cam 2
    # frame2 = cam2.video_capture.read()[1]
    # cv2.imshow("cam2", frame2)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    time.sleep(0.1)

cv2.destroyAllWindows()



