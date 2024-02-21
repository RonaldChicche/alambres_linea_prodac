# script para leer camara con opnecv y mostrar
import cv2
import numpy as np
import base64
import time
from onvif2 import ONVIFCamera, ONVIFService, ONVIFError
from web.ImagePro import measure_welding

# Configuración de la cámara
# IP de la cámara
IP = '192.168.90.108'
# Usuario y
USER = 'admin'
PASS = 'Bertek@206036'
wsl_dir = 'web/python-onvif2-zeep/wsdl'
# Crear el objeto de la cámara
cam = ONVIFCamera(IP, 80, USER, PASS, wsdl_dir=wsl_dir)
# Crear el objeto de servicio de medios
media_service = cam.create_media_service()
# Obtener el token del perfil
cam_token = media_service.GetProfiles()[0].token
# Obtener la URI del flujo
stream_uri = media_service.GetStreamUri({'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}, 'ProfileToken': cam_token})
# Crear la URL del flujo
url = f"rtsp://{USER}:{PASS}@{stream_uri.Uri.split('//')[1]}"
# Crear el objeto de captura de video
cap = cv2.VideoCapture(url)

while True:
    # Leer el fotograma de la cámara
    ret, frame = cap.read()
    # Si el fotograma se leyó correctamente
    if ret:
        # Procesar el fotograma
        img_ori, thresh, dy, mid, mid_fin = measure_welding(frame, debug=True)
        # print dimensions of each image
        print(f'img_ori: {img_ori.shape}')
        print(f'thresh: {thresh.shape}')
        print(f'dy: {dy.shape}')
        print(f'mid: {mid.shape}')
        print(f'mid_fin: {mid_fin.shape}')
        # Concatenate imgages
        img = np.concatenate((thresh, dy, mid, mid_fin), axis=0)
        # escalar la imagen
        img = cv2.resize(img, (int(img.shape[1]/2), int(img.shape[0]/2)))
        # Mostrar el fotograma procesado
        cv2.imshow('frame', img)
        cv2.imshow('frame_ori', img_ori)
        # Si se presiona la tecla 'q', salir del bucle
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        # Si no se leyó el fotograma, salir del bucle
        break




