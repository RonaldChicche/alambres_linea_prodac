from flask import Flask, Response, render_template
import os
import cv2
import time
import base64
import threading
import numpy as np
from flask import request
import cv2 as cv
# from .CamAIClass import CamAI
from onvif2 import ONVIFCamera, ONVIFService, ONVIFError
from .ImagePro import measure_welding, measure_tail


# Class for PTZ Web Apps
class PTZCamera:
    def __init__(self, ip, user, password, ptz=False):
        # Default values    
        self.ip = ip
        self.user = user
        self.password = password
        self.ptz_functions = ptz
        self.url = None
        self.current_file_path = os.path.dirname(os.path.abspath(__file__))
        self.wsdl_dir = os.path.join(self.current_file_path, 'python-onvif2-zeep', 'wsdl')
        # Camera response
        self.response = {
            'running': False,
            'trigger': False,
            'connected': False,
            'ok': False,
            'distancia': 0,
            'error': False,
            'error_code': 0,
            'imagen': None
        }
        # Threads
        self.video_stream = None
        self.thread_plc = None
        # Images
        self.video_capture = None
        self.capture = None
        self.imagen_resultado = None
        # PTZ services
        self.ptz_service = None
        self.imaging_service = None

        # Init Rutine
        # self.web_trigger = False
        self.response['connected'] = self.connect(self.ip, self.user, self.password)
        if self.response['connected']:
            self.start_video_capture()

    def __del__(self):
        if self.thread_plc is not None:
            self.thread_plc.join()
        if self.video_stream is not None:
            self.video_stream.join()
        if self.response['connected']:
            self.video_capture.release()
            self.disconnect()

    def connect(self, ip=None, user=None, password=None):
        try:
            # self.ip = ip
            # self.user = user
            # self.password = password
            self.onvif_cam = ONVIFCamera(host=self.ip, port=80, user=self.user, passwd=self.password, wsdl_dir=self.wsdl_dir)
            self.media_service = self.onvif_cam.create_media_service()
            self.cam_token = self.media_service.GetProfiles()[0].token
            # Get stream url
            stream_uri = self.media_service.GetStreamUri({'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}, 'ProfileToken': self.cam_token})
            self.url = f"rtsp://{self.user}:{self.password}@{stream_uri.Uri.split('//')[1]}"
            print(f"URI: {stream_uri.Uri}")
            if self.ptz_functions:
                self.ptz_service = self.onvif_cam.create_ptz_service()
                self.imaging_service = self.onvif_cam.create_imaging_service()
                self.presets = self.ptz_service.GetPresets(self.cam_token)
                self.set_velocity(0.5)
                # print presets names
                print(self.ip, "- Presets:")
                for preset in self.presets:
                    print("->", preset.Name)
            return True
        except Exception as e:
            print(f"Error connecting to camera {self.ip}/{self.user}/{self.password}: \n{e}")
            if self.url is not None:
                print(f"URI: {self.url}")
            return False
        
    def disconnect(self):
        self.onvif_cam.close()

    def start_video_capture(self):
        self.video_capture = cv2.VideoCapture(self.url)
        if not self.video_capture.isOpened():
            print("Error opening video stream or file")
            self.response['running'] = False
        self.response['running'] = True

    def read_video_capture(self, resize=False):
        ret, frame = self.video_capture.read()
        if not ret:
            print("Error capturing frame from video stream")
            return None
        if resize:
            frame = frame[0:480, 0:640]
        frame = cv2.imencode('.jpg', frame)[1].tobytes()
        frame_base64 = base64.b64encode(frame).decode('utf-8')
        return frame_base64

    def stop_video_capture(self):
        self.video_capture.release()
        self.response['running'] = False    

    def start_video_stream(self):
        # start thread
        self.video_stream = threading.Thread(target=self.generate_frames)
        self.video_stream.start()

    def generate_frames(self):
        video_stream = cv2.VideoCapture(self.url)
        while True:
            ret, frame = video_stream.read()
            if not ret:
                print("Error capturing frame from video stream")
                break

            frame = cv2.imencode('.jpg', frame)[1].tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def goto_preset(self, name):
        if self.ptz_functions:
            preset_name = name
            found = False
            for preset in self.presets:
                if preset.Name == preset_name:
                    print(f"Moving to {preset_name} ...", end=" ")
                    self.ptz_service.GotoPreset({'ProfileToken': self.cam_token, 'PresetToken': preset.token})
                    print('DONE')
                    found = True
            if not found:
                print(f"Preset {preset_name} not found")

    def get_state(self):
        if self.ptz_functions:
            status = self.ptz_service.GetStatus({'ProfileToken': self.cam_token})
            vid_status = self.imaging_service.GetImagingSettings({'VideoSourceToken': self.vid_token})
            print(vid_status)
            print(status)
            return status
        return None
    
    def save_preset(self):
        if self.ptz_functions:
            name = input('Ingrese nombre de nuevo preset: ')
            response = self.ptz_service.SetPreset({'ProfileToken': self.cam_token, 'PresetName': name})
            print(response)

    def set_autofocus(self):
        if self.ptz_functions:
            img_settings = self.imaging_service.GetImagingSettings({'VideoSourceToken': self.vid_token})
            img_settings.Focus.AutoFocusMode = 'AUTO'
            set_img_request = self.imaging_service.create_type('SetImagingSettings')
            set_img_request.VideoSourceToken = self.vid_token
            set_img_request.ImagingSettings = img_settings
            self.imaging_service.SetImagingSettings(set_img_request)
            print('Auto Focus mode ON')

    def set_velocity(self, velocity):
        if self.ptz_functions:
            if 0 <= velocity and velocity <=1:
                self.velocity = velocity
            else:
                print('Velocidad fuera de rango <min:0,max:1>')

    def move_up(self):
        if self.ptz_functions:
            print('Up')
            self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': self.velocity}}})
            time.sleep(0.1)
            self.ptz_service.Stop({'ProfileToken': self.cam_token})

    def move_down(self):
        if self.ptz_functions:
            #ptz = mycam.create_ptz_service()
            print('Down')
            self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': -self.velocity}}})
            time.sleep(0.1)
            self.ptz_service.Stop({'ProfileToken': self.cam_token})

    def move_left(self):
        if self.ptz_functions:
            #ptz = mycam.create_ptz_service()
            print('Left')
            self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': -self.velocity, 'y': 0}}})
            time.sleep(0.1)
            self.ptz_service.Stop({'ProfileToken': self.cam_token})

    def move_right(self):
        if self.ptz_functions:
            #ptz = mycam.create_ptz_service()
            print('Right')
            self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': self.velocity, 'y': 0}}})
            time.sleep(0.1)
            self.ptz_service.Stop({'ProfileToken': self.cam_token})

    def zoom_in(self):
        if self.ptz_functions:
            print('Zoom  IN')
            self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': 0}, 'Zoom': -1}})
            time.sleep(0.1)
            self.ptz_service.Stop({'ProfileToken': self.cam_token})

    def zoom_out(self):
        if self.ptz_functions:
            print('Zoom OUT')
            self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': 0}, 'Zoom': 1}})
            time.sleep(0.1)
            self.ptz_service.Stop({'ProfileToken': self.cam_token})



class CameraWelding(PTZCamera):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password, ptz=True)
        self.run = True
        self.name = 'Welding Camera'

    def __del__(self):
        self.stop()

    def start_plc_thread(self, plc_parser):
        self.run = True
        self.plc_parser = plc_parser
        self.thread_plc = threading.Thread(target=self.plc_control)
        self.thread_plc.start()

    def stop(self):
        self.run = False
        if self.cap is not None:
            self.cap.release()
        if self.thread_plc is not None:
            self.thread_plc.join()
    
    def update_response(self):
        # update self.response keys with plc_parser.ctw_cam
        self.response['ok'] = self.plc_parser.stw_cam["OK_WELD"]
        self.response['distancia'] = self.plc_parser.cam_struc["WELD_MEASURE"]
        self.response['error'] = self.plc_parser.stw_cam["ERROR_WELD"]
        self.response['error_code'] = self.plc_parser.cam_struc["ERROR"]
        self.response['imagen'] = self.imagen_resultado

    def plc_control(self):
        self.prev_state = False
        # connect streaming ...
        # self.video_stream = cv2.VideoCapture(self.url)
        while self.run:            
            # Verificar coneccion e intentar reconectar
            if self.response['connected'] == False:
                self.response['connected'] = self.connect(self.ip, self.user, self.password)
                if not self.response['connected']:
                    self.plc_parser.cam_struc["ERROR"] = 1
                    time.sleep(5)
                    continue
            
            
            self.response['trigger'] = self.plc_parser.ctw_cam["TRIG_WELD"]
            if self.plc_parser.ctw_cam["TRIG_WELD"] == False:
                self.plc_parser.stw_cam["OK_WELD"] = False
                self.plc_parser.stw_cam["ERROR_WELD"] = False
                self.plc_parser.cam_struc["WELD_MEASURE"] = 0
                self.plc_parser.cam_struc["ERROR"] = 0
                self.prev_state = False

            if self.plc_parser.ctw_cam['TRIG_WELD'] ^ self.prev_state:  
                if self.prev_state == True:
                    continue  
                self.cap = cv2.VideoCapture(self.url)
                self.response['connected'] = self.cap.isOpened()
                # Error de conexion
                if not self.cap.isOpened():
                    print("Error opening video stream or file")
                    self.plc_parser.stw_cam["OK_WELD"] = False
                    self.plc_parser.stw_cam["ERROR_WELD"] = True
                    self.plc_parser.cam_struc["WELD_MEASURE"] = -1
                    self.plc_parser.cam_struc["ERROR"] = 1
                    self.prev_state = self.plc_parser.ctw_cam["TRIG_WELD"]
                    self.ptz_connected = False
                    continue
                dist, err, img_res = self.measure_border()
                # Process image cap for web
                img_res = cv2.imencode('.jpg', img_res)[1].tobytes()
                img_res = base64.b64encode(img_res).decode('utf-8')
                self.imagen_resultado = img_res
                
                if err == 0:
                    self.plc_parser.stw_cam["OK_WELD"] = True
                    self.plc_parser.stw_cam["ERROR_WELD"] = False
                    self.plc_parser.cam_struc["WELD_MEASURE"] = dist
                else:
                    self.plc_parser.stw_cam["OK_WELD"] = False
                    self.plc_parser.stw_cam["ERROR_WELD"] = True
                    self.plc_parser.cam_struc["WELD_MEASURE"] = -1

                self.plc_parser.cam_struc["ERROR"] = err
                self.prev_state = self.plc_parser.ctw_cam["TRIG_WELD"]
                self.cap.release()
                # Update response
                self.update_response()
                print("-----------------------------------------------------", self.plc_parser.cam_struc)

    def plc_control2(self):
        self.prev_state = False
        while True:
            # Verificar coneccion e intentar reconectar
            if self.response['connected'] == False:
                self.response['connected'] = self.connect(self.ip, self.user, self.password)
                if not self.response['connected']:
                    self.plc_parser.cam_struc["ERROR"] = 1
                    time.sleep(5)
                    continue

            if self.web_trigger == False:
                self.response['ok'] = False
                self.response['error'] = False
                self.response['error_code'] = 0
                self.response['distancia'] = 0
                self.response['imagen'] = None
                self.prev_state = False
                # print("---- Terminated  -> ", self.response['distancia'])

            if self.web_trigger ^ self.prev_state: 
                self.prev_state = self.web_trigger   
                self.start_video_capture()
                # Error de conexion
                if not self.response['running']:
                    print("Error opening video stream or file")                    
                    self.response['ok'] = False
                    self.response['error'] = True
                    self.response['err_code'] = 1
                    self.response['dist'] = -1
                    self.response['img'] = None
                    continue
                # dist, err = self.measure_weld()
                frame_base64 = self.read_video_capture(resize=True)

                dist = 34.5 + self.response['distancia']
                err = 0

                if err == 0:
                    self.response['ok'] = True
                    self.response['error'] = False
                    self.response['distancia'] = dist
                else:
                    self.response['ok'] = False
                    self.response['error'] = True
                    self.response['distancia'] = -1

                self.response['error_code'] = err
                self.response['imagen'] = frame_base64
                self.stop_video_capture()
                print("-----------------------------------------------------", "Shooted")

    def measure_border(self):
        """Try to measure the welding 3 times, if it fails return an error
            Returns:
            dist: distance between the welding and the center of the image
            dx1: distance between the welding and the left border of the image
            dx2: distance between the welding and the right border of the image
            - Errors:
                0: No error
                1: Imagen en formato incorrecto
                2: Fallo en la deteccion de bordes
                3: Lectura incorrecta
        """
        lenghts = []
        img_return = []
        self.goto_preset('Machine')
        for i in range(5):
            ret, img = self.cap.read()
            if ret:
                img_res, dist, dx1, dx2, err = measure_welding(img)
                if err == 0:
                    lenghts.append(dist)                    
                img_return.append(img_res)    # Return to the web page
            else:
                print('Error capturing frame from video stream')
        
        if len(img_return) > 0:
            # fusiona las imagenes en una sola en vertical
            img_return = np.concatenate(img_return, axis=0)
        else: 
            # make a black image that says no image
            img_return = np.zeros((480, 640, 3), np.uint8)
            cv2.putText(img_return, 'No image', (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            

        # Verify if the measure is correct
        if len(lenghts) == 0 or np.mean(lenghts) < 0:
            err = 3
            return -1, err, img_return
            
        return np.mean(lenghts), err, img_return

    def start(self, app):

        # Send a list of names on connection with a new client
        # @self.socketio.on('connect', namespace='/welding_cam')
        # def connect():
        #     print("Client connected")
        #     self.camera_con = False
        #     # self.presets = self.load_presets()
        #     self.socketio.emit('init', {'streaming_state': self.camera_con, 'presets': self.presets}, namespace='/welding_cam')

        @app.route('/states_welding', methods=['GET'])
        def states_welding():
            # update camera_response keys with plc_parser
            self.update_response()

            # return sel.cam_resp consider that cam_resp is a dict and i only want to send its keys with their values
            return {'status': 200, 'camera_response': self.response}

        # Handle post /shoot_welding request
        @app.route('/shoot_welding', methods=['POST'])
        def shoot_welding():
            self.web_trigger = not self.web_trigger
            print("TRIG", self.web_trigger)
            return {'status': 200}
            # try:
            #     # data = dict(request.get_json())
            #     # print(data)
            #     # dist, dx1, dx2 = self.measure_weld()
            #     # print(dist, dx1, dx2)
            #     # return {'status': 200, 'distance': dist, 'dx1': dx1, 'dx2': dx2}
            #     self.cap = cv2.VideoCapture(0)
            #     ret, img = self.cap.read()
            #     if ret:
            #         img_base64 = base64.b64encode(img).decode('utf-8')
            #         self.socketio.emit('image_shoot', {'frame': img_base64, 'dist': 34.6}, namespace='/welding_cam')
            #         return {'status': 200}
            #     else:
            #         return {'status': 500, 'error': 1}
            # except Exception as e:
            #     return {'status': 500, 'error': str(e)}

        # Define the route for the video stream
        # @app.route('/video_feed')
        # def video_feed():
        #     cap = cv2.VideoCapture(0)
        #     while True:
        #         ret, frame = cap.read()
        #         if not ret:
        #             print("Error capturing frame from video stream")
        #             break

        #         frame = cv2.imdecode('.jpg', frame)[1].tobytes()
        #         socketio.emit('video_frame', frame, namespace='/video')
        
        @app.route('/video_feed', methods=['POST'])
        def video_feed():
            return Response(self.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @app.route('/video_stop')
        def video_stop():
            try:
                self.stop_video_capture()
                return {'status': 200}
            except Exception as e:
                return {'status': 500, 'error': str(e)}
        
        @app.route('/move_up')
        def move_up():
            self.move_up()
            return {'status': 200}
        
        @app.route('/move_down')
        def move_down():
            self.move_down()
            return {'status': 200}
        
        @app.route('/move_left')
        def move_left():
            self.move_left()
            return {'status': 200}
        
        @app.route('/move_right')
        def move_right():
            self.move_right()
            return {'status': 200}
        
        @app.route('/goto_preset', methods=['POST'])
        def goto_preset():
            name = request.json['name']
            self.goto_preset(name)
            return {'status': 200}

        @app.route('/change_url', methods=['POST'])
        def change_url():
            url = request.json['url']
            self.change_url(url)
            return {'status': 200}

        @app.route('/get_state', methods=['GET'])
        def get_state():
            status = self.get_state()
            return {'status': 200, 'state': status}

        @app.route('/save_preset', methods=['POST'])
        def save_preset():
            self.save_preset()
            return {'status': 200}

        @app.route('/weld_measure', methods=['GET'])
        def web_weld_measure():
            """Try to measure the welding 5 times, if it fails return an error"""
            self.cap = cv2.VideoCapture(self.url)
            self.response['connected'] = self.cap.isOpened()
            # Error de conexion
            if not self.cap.isOpened():
                return {'status': 500, 'error': 1}
            
            lenght_weld, error, img_res = self.measure_border()
            # Process image cap for web
            img_res = cv2.imencode('.jpg', img_res)[1].tobytes()
            img_res = base64.b64encode(img_res).decode('utf-8')
            self.imagen_resultado = img_res
            print(f"Status: {200}, lenght: {lenght_weld}, error:{error}")
            
            return {'status': 200, 'lenght': lenght_weld, 'img': img_res, 'error': error}
            
            

class CameraTail(PTZCamera):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password, ptz=False)
        self.run = True
        self.name = 'Tail Camera'

    def __del__(self):
        self.stop()

    def start_plc_thread(self, plc_parser):
        self.plc_parser = plc_parser
        self.thread_plc = threading.Thread(target=self.plc_control)
        self.thread_plc.start()

    def stop(self):
        self.run = False
        if self.cap is not None:
            self.cap.release()
        if self.thread_plc is not None:
            self.thread_plc.join()

    def update_response(self):
        # update self.response keys with plc_parser.ctw_cam
        self.response['ok'] = self.plc_parser.stw_cam["OK_TAIL"]
        self.response['distancia'] = self.plc_parser.cam_struc["TAIL_MEASURE"]
        self.response['error'] = self.plc_parser.stw_cam["ERROR_TAIL"]
        self.response['error_code'] = self.plc_parser.cam_struc["ERROR"]
        self.response['imagen'] = self.imagen_resultado

    # Thread plc
    def plc_control(self):
        self.prev_state = False
        while self.run:
            # Verificar coneccion e intentar reconectar
            if self.response['connected'] == False:
                self.response['connected'] = self.connect(self.ip, self.user, self.password)
                if not self.response['connected']:
                    self.plc_parser.cam_struc["ERROR"] = 1
                    time.sleep(5)
                    continue

            # print(f"Esperando trigger --------------------------------------------------------------------------{self.plc_parser.ctw_cam['TRIG_TAIL']}")
            self.response['trigger'] = self.plc_parser.ctw_cam["TRIG_TAIL"]
            if self.plc_parser.ctw_cam["TRIG_TAIL"] == False:
                self.plc_parser.stw_cam["OK_TAIL"] = False
                self.plc_parser.stw_cam["ERROR_TAIL"] = False
                self.plc_parser.cam_struc["TAIL_MEASURE"] = 0
                self.plc_parser.cam_struc["ERROR"] = 0
                self.prev_state = False

            if self.plc_parser.ctw_cam["TRIG_TAIL"] ^ self.prev_state:
                if self.prev_state == True:
                    continue
                self.cap = cv2.VideoCapture(self.url)
                # Error de conexion
                if not self.cap.isOpened():
                    print("Error opening video stream or file")
                    self.plc_parser.stw_cam["OK_TAIL"] = False
                    self.plc_parser.stw_cam["ERROR_TAIL"] = True
                    self.plc_parser.cam_struc["TAIL_MEASURE"] = -1
                    self.plc_parser.cam_struc["ERROR"] = 1
                    self.prev_state = self.plc_parser.ctw_cam["TRIG_TAIL"]
                    self.camera_con = False
                    continue
                    
                lenght_tail, error, img_res = self.measure_border()
                # Process image cap for web
                # if img_res is not None:
                img_res = cv2.imencode('.jpg', img_res)[1].tobytes()
                img_res = base64.b64encode(img_res).decode('utf-8')
                self.imagen_resultado = img_res
                # else:
                #     img_res = None

                if error == 0:                    
                    self.plc_parser.stw_cam["OK_TAIL"] = True
                    self.plc_parser.stw_cam["ERROR_TAIL"] = False
                    self.plc_parser.cam_struc["TAIL_MEASURE"] = lenght_tail
                else:
                    self.plc_parser.stw_cam["OK_TAIL"] = False
                    self.plc_parser.stw_cam["ERROR_TAIL"] = True
                    self.plc_parser.cam_struc["TAIL_MEASURE"] = -1
                    print("++++++++++++++++++", error)
                
                self.plc_parser.cam_struc["ERROR"] = error
                self.prev_state = self.plc_parser.ctw_cam["TRIG_TAIL"]
                # Update response
                self.update_response()
                self.cap.release()
                print("-----------------------------------------------------", self.plc_parser.cam_struc)

            # else:
                # print("-----------------------------------------------------", self.plc_parser.cam_struc)
            time.sleep(0.5)
    
    def plc_control2(self):
        self.prev_state = False
        while True:
            # Verificar coneccion e intentar reconectar
            if self.response['connected'] == False:
                self.response['connected'] = self.connect(self.ip, self.user, self.password)
                if not self.response['connected']:
                    self.plc_parser.cam_struc["ERROR"] = 1
                    time.sleep(5)
                    continue

            if self.web_trigger == False:
                self.response['ok'] = False
                self.response['error'] = False
                self.response['error_code'] = 0
                self.response['distancia'] = 0
                self.response['imagen'] = None
                self.prev_state = False
                # print("---- Terminated  -> ", self.response['distancia'])


            if self.web_trigger ^ self.prev_state: 
                self.prev_state = self.web_trigger   
                self.start_video_capture()
                # Error de conexion
                if not self.response['running']:
                    print("Error opening video stream or file")                    
                    self.response['ok'] = False
                    self.response['error'] = True
                    self.response['err_code'] = 1
                    self.response['dist'] = -1
                    self.response['img'] = None
                    continue
                # dist, err = self.measure_weld()
                frame_base64 = self.read_video_capture(resize=True)

                dist = 34.5 + self.response['distancia']
                err = 0

                if err == 0:
                    self.response['ok'] = True
                    self.response['error'] = False
                    self.response['distancia'] = dist
                else:
                    self.response['ok'] = False
                    self.response['error'] = True
                    self.response['distancia'] = -1

                self.response['error_code'] = err
                self.response['imagen'] = frame_base64
                self.stop_video_capture()
                print("-----------------------------------------------------", "Shooted")

    def measure_border(self):
        """Try to measure the welding 5 times, if it fails return an error
            Returns:
            lenght_tail: lenght of the tail
            -  Error code:
                0: No error
                1: Imagen en formato incorrecto
                2: Fallo en la deteccion de bordes
                3: Lectura incorrecta
        """
        lenghts = []
        img_return = []
        error = 0
        for i in range(5):
            ret, frame = self.cap.read()
            if ret:
                img, lenght_tail, error = measure_tail(frame)
                if error == 0:
                    lenghts.append(lenght_tail)
                img_return.append(img) ### For de web page
        
        if len(img_return) > 0:
            # fusiona las imagenes en una sola en vertical
            img_return = np.concatenate(img_return, axis=0)
        else: 
            # make a black image that says no image
            img_return = np.zeros((480, 640, 3), np.uint8)
            cv2.putText(img_return, 'No image', (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        

        # Verify if measure is correct
        if len(lenghts) == 0 or np.mean(lenghts) < 0:
            error = 3
            return 0, error, img_return
        
        return np.mean(lenghts), error, img_return

    def start(self, app):
        @app.route('/states_cola', methods=['GET'])
        def states_tail():
            # update camera_response keys
            self.update_response()

            # return sel.cam_resp consider that cam_resp is a dict and i only want to send its keys with their values
            return {'status': 200, 'camera_response': self.response}

        # Handle post /shoot_welding request
        @app.route('/shoot_cola', methods=['POST'])
        def shoot_tail():
            self.web_trigger = not self.web_trigger
            print("TRIG", self.web_trigger)
            return {'status': 200}

        @app.route('/tail_measure', methods=['GET'])
        def web_tail_measure():
            """Try to measure the welding 5 times, if it fails return an error"""
            self.cap = cv2.VideoCapture(self.url)
            self.response['connected'] = self.cap.isOpened()
            # Error de conexion
            if not self.cap.isOpened():
                return {'status': 500, 'error': 1}
            
            lenght_tail, error, img_res = self.measure_border()
            # if error == 0:
            # Process image cap for web
            img_res = cv2.imencode('.jpg', img_res)[1].tobytes()
            img_res = base64.b64encode(img_res).decode('utf-8')
            self.imagen_resultado = img_res
            
            print(f"Status: {200}, lenght: {lenght_tail}, error:{error}")
            return {'status': 200, 'lenght': lenght_tail, 'img': img_res, 'error': error}