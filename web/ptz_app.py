from flask import Flask, Response, render_template
import os
import cv2
import time
import threading
import numpy as np
from flask import request
# from .CamAIClass import CamAI
from onvif2 import ONVIFCamera, ONVIFService, ONVIFError
from .ImagePro import measure_welding, measure_tail


class PTZWebApp:
    def __init__(self):
        self.url = 0
        self.presets = None
        self.current_preset = None
        self.velocity = 1
        self.num_im = 0
        self.video_capture = None
        self.image = None
        self.connected = False
        self.ip = "192.168.90.108"
        self.user = "admin"
        self.password = "Bertek@206036"
        self.url = "rtsp://admin:Bertek@206036@192.168.90.108"
        self.current_file_path = os.path.dirname(os.path.abspath(__file__))        
        self.wsdl_dir = os.path.join(self.current_file_path, 'python-onvif2-zeep', 'wsdl')

        try:
            self.connect()
        except Exception as e:
            print(f"Error connecting to camera: {e}")
            self.camera_con = False
    
    def __del__(self):
        self.stop_video_capture()
        cv2.destroyAllWindows()
        # stop thread
        self.thread_plc.join()


    def connect(self):
        self.onvif_cam = ONVIFCamera(self.ip, 80, self.user, self.password, wsdl_dir=self.wsdl_dir)
        self.ptz_service = self.onvif_cam.create_ptz_service()
        self.media_service = self.onvif_cam.create_media_service()
        self.imaging_service = self.onvif_cam.create_imaging_service()
        self.cam_token = self.media_service.GetProfiles()[0].token
        self.load_presets()
        self.camera_con = True
        

    def start_video_capture(self, data:dict):
        if self.connected == False:
            self.ip = data['ip']
            self.user = data['user']
            self.password = data['pass']
            self.url = f'rtsp://{self.user}:{self.password}@{self.ip}'
            self.wsdl_dir = os.path.join(self.current_file_path, 'python-onvif2-zeep', 'wsdl')
            try:
                self.onvif_cam = ONVIFCamera(self.ip, 80, self.user, self.password, wsdl_dir=self.wsdl_dir)
                print(f"ONVIF: {self.onvif_cam}")
                self.ptz_service = self.onvif_cam.create_ptz_service()
                self.media_service = self.onvif_cam.create_media_service()
                self.imaging_service = self.onvif_cam.create_imaging_service()
                self.cam_token = self.media_service.GetProfiles()[0].token
                self.vid_token = self.media_service.GetVideoSources()[0].token
                print(f"Connecting to -> {self.url} ")
            except Exception as e:
                print(f"Error connecting to camera: {e}")
                

    def stop_video_capture(self):
        # stop video capture and onvif camera
        if self.video_capture is not None:  
            self.video_capture.release()
            self.video_capture = None
            self.connected = False

    def plc_control(self):
        self.prev_state = False
        while True:
            # Verificar coneccion e intentar reconectar
            if self.camera_con == False:
                try:
                    self.connect()
                except Exception as e:
                    print(f"Error connecting to camera: {e}")
                    self.camera_con = False
                    self.plc_parser.cam_struc["ERROR"] = 1
                    time.sleep(5)
                    continue
            
            if self.plc_parser.ctw_cam["TRIG_WELD"] == False:
                self.plc_parser.stw_cam["OK_WELD"] = False
                self.plc_parser.stw_cam["ERROR_WELD"] = False
                self.plc_parser.cam_struc["WELD_MEASURE"] = 0
                self.plc_parser.cam_struc["ERROR"] = 0
                self.prev_state = False

            if self.plc_parser.ctw_cam['TRIG_WELD'] ^ self.prev_state:    
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
                dist, err = self.measure_weld()
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
                print("-----------------------------------------------------", self.plc_parser.cam_struc)
            
        
    # thread declaration and initialization
    def start_plc_thread(self, plc_parser):
        self.plc_parser = plc_parser
        self.thread_plc = threading.Thread(target=self.plc_control)
        self.thread_plc.start()

    def load_presets(self):
        self.presets = self.ptz_service.GetPresets(self.cam_token)
        list_presets = []
        if self.presets:
            print("Available PTZ presets:")
            for preset in self.presets:
                print(f"- {preset.Name}")
                list_presets.append(preset.Name)
            return list_presets
        else: 
            print("No available presets")
            return None

    def goto_preset(self, name):
        preset_name = name  # Replace with the name of the preset you want to use
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
        status = self.ptz_service.GetStatus({'ProfileToken': self.cam_token})
        vid_status = self.imaging_service.GetImagingSettings({'VideoSourceToken': self.vid_token})
        print(vid_status)
        print(status)
        return status
    
    def save_preset(self):
        name = input('Ingrese nombre de nuevo preset: ')
        response = self.ptz_service.SetPreset({'ProfileToken': self.cam_token, 'PresetName': name})
        print(response)

    def set_autofocus(self):
        img_settings = self.imaging_service.GetImagingSettings({'VideoSourceToken': self.vid_token})
        img_settings.Focus.AutoFocusMode = 'AUTO'
        set_img_request = self.imaging_service.create_type('SetImagingSettings')
        set_img_request.VideoSourceToken = self.vid_token
        set_img_request.ImagingSettings = img_settings
        self.imaging_service.SetImagingSettings(set_img_request)
        print('Auto Focus mode ON')
    
    def set_velocity(self, velocity):
        if 0 <= velocity and velocity <=1:
            self.velocity = velocity
        else:
            print('Velocidad fuera de rango <min:0,max:1>')

    def move_up(self):
        print('Up')
        self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': self.velocity}}})
        time.sleep(0.1)
        self.ptz_service.Stop({'ProfileToken': self.cam_token})

    # Mover la cámara hacia abajo
    def move_down(self):
        #ptz = mycam.create_ptz_service()
        print('Down')
        self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': -self.velocity}}})
        time.sleep(0.1)
        self.ptz_service.Stop({'ProfileToken': self.cam_token})

    # Mover la cámara hacia la izquierda
    def move_left(self):
        #ptz = mycam.create_ptz_service()
        print('Left')
        self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': -self.velocity, 'y': 0}}})
        time.sleep(0.1)
        self.ptz_service.Stop({'ProfileToken': self.cam_token})

    # Mover la cámara hacia la derecha
    def move_right(self):
        #ptz = mycam.create_ptz_service()
        print('Right')
        self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': self.velocity, 'y': 0}}})
        time.sleep(0.1)
        self.ptz_service.Stop({'ProfileToken': self.cam_token})

    def zoom_in(self):
        print('Zoom  IN')
        self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': 0}, 'Zoom': -1}})
        time.sleep(0.1)
        self.ptz_service.Stop({'ProfileToken': self.cam_token})

    def zoom_out(self):
        print('Zoom OUT')
        self.ptz_service.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': 0}, 'Zoom': 1}})
        time.sleep(0.1)
        self.ptz_service.Stop({'ProfileToken': self.cam_token})

    def change_url(self, url):
        self.url = url
        self.stop_video_capture()
        self.start_video_capture()

    def measure_weld(self):
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
        
        # Verify if the measure is correct
        if len(lenghts) == 0 or np.mean(lenghts) < 0:
            err = 3
            return -1, err
            
        return np.mean(lenghts), err


    def start(self, app):
        # Define the route for the video stream
        @app.route('/video_feed')
        def video_feed():
            def generate():
                prev_frame = None
                while True:
                    if self.video_capture is not None:
                        # Capture a frame from the video stream
                        ret, frame = self.video_capture.read()

                        if ret:
                            # Encode the frame as a JPEG image
                            ret, jpeg = cv2.imencode('.jpg', frame)
                            self.image = frame
                            if ret:
                                # Yield the JPEG image as a byte stream
                                yield (b'--frame\r\n'
                                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                                prev_frame = frame
                            else:
                                print('Error encoding frame as JPEG')
                        else:
                            print('Error capturing frame from video stream')
                    else:
                        if prev_frame is not None:
                            # Create a black image of the same size as the previous frame
                            black_frame = np.zeros_like(prev_frame)

                            # Encode the black frame as a JPEG image
                            ret, jpeg = cv2.imencode('.jpg', black_frame)

                            if ret:
                                # Yield the JPEG image as a byte stream
                                yield (b'--frame\r\n'
                                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                            else:
                                print('Error encoding black frame as JPEG')
                        # else:
                            # print('No previous frame to use for black image')

            # Return the byte stream as a Flask response
            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @app.route('/video_start', methods=['POST'])
        def video_start():
            try:
                data = dict(request.get_json())
                print(data)
                self.start_video_capture(data)
                list_presets = self.load_presets()
                print(list_presets)
                self.connected = True
                print(self.connected)
                return {'status': 200, 'presets': list_presets}
            except Exception as e:
                return {'status': 500, 'error': str(e)}

        
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
        def weld_measure():
            """Try to measure the welding 3 times, if it fails return an error"""
            dist, dx1, dx2 = self.measure_weld()
            if dist is not None:
                return {'status': 200, 'distance': dist, 'dx1': dx1, 'dx2': dx2}
            
            return {'status': 500, 'error': 'Low accuracy'}

        @app.route('/border_measure', methods=['GET'])
        def border_measure():
            """Try to measure the welding 5 times, if it fails return an error"""
            lenght_tail, error = self.measure_border()
            if error == 0:
                return {'status': 200, 'lenght': lenght_tail}
            
            return {'status': 500, 'error': 'Low accuracy'}
            
            


class PTZWebApp2:
    def __init__(self, ip, port, user, password):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.camera = None
        self.cap = None
        self.current_file_path = os.path.dirname(os.path.abspath(__file__))
        self.wsl_dir = os.path.join(self.current_file_path, 'python-onvif2-zeep', 'wsdl')
        try: 
            self.connect()
        except Exception as e:
            print(f"Error connecting to camera: {e}")
            self.camera_con = False

    def __del__(self):
        # stop thread
        self.thread_plc.join()
        

    def connect(self):
        self.camera = ONVIFCamera(self.ip, self.port, self.user, self.password, wsdl_dir=self.wsl_dir)
        self.url = self.get_stream_url()
        print("URL Stream:", self.url)
        self.camera_con = True

    def get_service_info(self):
        return self.camera.devicemgmt.GetServices(False)

    def get_stream_url(self):
        media_service = self.camera.create_media_service()
        profiles = media_service.GetProfiles()
        main_profile = profiles[0]
        stream_uri = media_service.GetStreamUri({'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}, 'ProfileToken': main_profile.token})
        return f"rtsp://{self.user}:{self.password}@{stream_uri.Uri.split('//')[1]}"

    # Thread plc
    def plc_control(self):
        self.prev_state = False
        while True:
            # Verificar coneccion e intentar reconectar
            if self.camera_con == False:
                try:
                    self.connect()
                except Exception as e:
                    print(f"Error connecting to camera: {e}")
                    self.camera_con = False
                    self.plc_parser.cam_struc["ERROR"] = 1
                    time.sleep(5)
                    continue

            # print(f"Esperando trigger --------------------------------------------------------------------------{self.plc_parser.ctw_cam['TRIG_TAIL']}")
            if self.plc_parser.ctw_cam["TRIG_TAIL"] == False:
                self.plc_parser.stw_cam["OK_TAIL"] = False
                self.plc_parser.stw_cam["ERROR_TAIL"] = False
                self.plc_parser.cam_struc["TAIL_MEASURE"] = 0
                self.plc_parser.cam_struc["ERROR"] = 0
                self.prev_state = False

            if self.plc_parser.ctw_cam["TRIG_TAIL"] ^ self.prev_state:
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
                    
                lenght_tail, error = self.measure_border()
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
                self.cap.release()
                print("-----------------------------------------------------", self.plc_parser.cam_struc)

            # else:
                # print("-----------------------------------------------------", self.plc_parser.cam_struc)
            time.sleep(0.5)

    def start_plc_thread(self, plc_parser):
        self.plc_parser = plc_parser
        self.thread_plc = threading.Thread(target=self.plc_control)
        self.thread_plc.start()
    
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
        for i in range(5):
            ret, frame = self.cap.read()
            if ret:
                img, lenght_tail, error = measure_tail(frame)
                if error == 0:
                    lenghts.append(lenght_tail)
                    img_return.append(img) ### For de web page
        
        # Verify if measure is correct
        if len(lenghts) == 0 or np.mean(lenghts) < 0:
            error = 3
            return 0, error
        
        return np.mean(lenghts), error


    def show_video(self):
        while True:
            ret, frame = self.cap.read()
            if ret:
                cv2.imshow('frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print('Error capturing frame from video stream')
        cv2.destroyAllWindows()