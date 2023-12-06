import cv2
import time
from enum import Enum
from onvif import ONVIFCamera, ONVIFService, ONVIFError
from ImgProcessing import measure_welding


class CamAI():
    def __init__(self, cam_ip, user, password) -> None:
        self.cam_ip = '192.168.90.108'
        self.cam_port = 80
        self.user = 'admin'
        self.pswd = 'Bertek@206036'
        self.capture = cv2.VideoCapture(f'rtsp://{self.user}:{self.pswd}@{self.cam_ip}')
        self.mycam = ONVIFCamera(self.cam_ip, self.cam_port, self.user, self.pswd)
        self.ptz = self.mycam.create_ptz_service()
        self.media = self.mycam.create_media_service()
        self.imaging = self.mycam.create_imaging_service()
        self.cam_token = self.media.GetProfiles()[0].token
        self.vid_token = self.media.GetVideoSources()[0].token
        self.presets = None
        self.current_preset = None
        self.velocity = 1

    def key_control(self, key):
        if key == ord('w'):
            self.move_up()
        elif key == ord('s'):
            self.move_down()
        elif key == ord('a'):
            self.move_left() 
        elif key == ord('d'):
            self.move_right()
        elif key == ord('r'):
            print('Saved')
            filename = f'frame_{image_number}.png'
            cv2.imwrite(filename, img)
            print(f"Saved {filename}")
            image_number += 1
        elif key == ord('f'):
            print('Autofocus')
            self.set_autofocus()
            
        elif key == ord('g'):
            self.get_state()
        elif key == ord('i'):
            self.zoom_in()
        elif key == ord('o'):
            self.zoom_out()
        elif key == ord('1'):
            self.goto_preset('Zero')
            self.current_preset = 'Zero'
        elif key == ord('2'):
            self.goto_preset('Init')
            self.current_preset = 'Init'
        elif key == ord('3'):
            self.goto_preset('Support')
            self.current_preset = 'Support'
        elif key == ord('4'):
            self.goto_preset('Machine')
            self.current_preset = 'Machine'
        elif key == ord('5'):
            self.goto_preset('Wire_out')
            self.current_preset = 'Wire_out'
        elif key == ord('6'):
            self.goto_preset('Esmeril')
            self.current_preset = 'Esmeril'
    

    def load_presets(self):
        self.presets = self.ptz.GetPresets(self.cam_token)
        if self.presets:
            print("Available PTZ presets:")
            for preset in self.presets:
                print(f"- {preset.Name}")
        else: 
            print("No available presets")

    def goto_preset(self, name):
        preset_name = name  # Replace with the name of the preset you want to use
        found = False
        for preset in self.presets:
            if preset.Name == preset_name:
                print(f"Moving to {preset_name} ...", end=" ")
                self.ptz.GotoPreset({'ProfileToken': self.cam_token, 'PresetToken': preset.token})
                print('DONE')
                found = True
        if not found:
            print(f"Preset {preset_name} not found")

    def get_state(self):
        status = self.ptz.GetStatus({'ProfileToken': self.cam_token})
        vid_status = self.imaging.GetImagingSettings({'VideoSourceToken': self.vid_token})
        print(vid_status)
        print(status)
        return status
    
    def save_preset(self):
        name = input('Ingrese nombre de nuevo preset: ')
        response = self.ptz.SetPreset({'ProfileToken': self.cam_token, 'PresetName': name})
        print(response)

    def set_autofocus(self):
        img_settings = self.imaging.GetImagingSettings({'VideoSourceToken': self.vid_token})
        img_settings.Focus.AutoFocusMode = 'AUTO'
        set_img_request = self.imaging.create_type('SetImagingSettings')
        set_img_request.VideoSourceToken = self.vid_token
        set_img_request.ImagingSettings = img_settings
        self.imaging.SetImagingSettings(set_img_request)
        print('Auto Focus mode ON')
    
    def set_velocity(self, velocity):
        if 0 <= velocity and velocity <=1:
            self.velocity = velocity
        else:
            print('Velocidad fuera de rango <min:0,max:1>')

    def move_up(self):
        print('Up')
        self.ptz.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': self.velocity}}})
        time.sleep(0.1)
        self.ptz.Stop({'ProfileToken': self.cam_token})

    # Mover la cámara hacia abajo
    def move_down(self):
        #ptz = mycam.create_ptz_service()
        print('Down')
        self.ptz.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': -self.velocity}}})
        time.sleep(0.1)
        self.ptz.Stop({'ProfileToken': self.cam_token})

    # Mover la cámara hacia la izquierda
    def move_left(self):
        #ptz = mycam.create_ptz_service()
        print('Left')
        self.ptz.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': -self.velocity, 'y': 0}}})
        time.sleep(0.1)
        self.ptz.Stop({'ProfileToken': self.cam_token})

    # Mover la cámara hacia la derecha
    def move_right(self):
        #ptz = mycam.create_ptz_service()
        print('Right')
        self.ptz.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': self.velocity, 'y': 0}}})
        time.sleep(0.1)
        self.ptz.Stop({'ProfileToken': self.cam_token})

    def zoom_in(self):
        print('Zoom  IN')
        self.ptz.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': 0}, 'Zoom': -1}})
        time.sleep(0.1)
        self.ptz.Stop({'ProfileToken': self.cam_token})

    def zoom_out(self):
        print('Zoom OUT')
        self.ptz.ContinuousMove({'ProfileToken': self.cam_token, 'Velocity': {'PanTilt': {'x': 0, 'y': 0}, 'Zoom': 1}})
        time.sleep(0.1)
        self.ptz.Stop({'ProfileToken': self.cam_token})


# cap = cv2.VideoCapture('rtsp://admin:Bertek@206036@192.168.90.108')
# mycam = ONVIFCamera('192.168.90.108', 80, 'BERTEK', 'Bertek@2060', '/wsdl/')

# Configura la dirección IP, puerto, nombre de usuario y contraseña de la cámara ONVIF
CAMERA_IP = '192.168.90.108'
CAMERA_PORT = 80
USERNAME = 'admin'
PASSWORD = 'Bertek@206036'

camera = CamAI(CAMERA_IP, USERNAME, PASSWORD)
camera.load_presets()

if __name__ == '__main__':
    print(camera.cam_token)
    time.sleep(3)
    print("Usa las teclas de dirección (arriba, abajo, izquierda, derecha) para mover la cámara ONVIF.")
    print("Presiona 'Q' para salir.")

    run = True
    while run:    
        try:
            success, img = camera.capture.read()
            if camera.current_preset == 'Machine':
                img_fin, dist, dx1, dx2 = measure_welding(img)
                cv2.imshow("distance", img_fin)

            cv2.imshow("Image", img)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): 
                run = False
                break
            #else: keyboard.on_press(move_camera)
            else:
                camera.key_control(key)

        except cv2.error as e:
            print(f"OpenCV Error: {e}")

        except KeyboardInterrupt:
            run = False


    cv2.destroyAllWindows()    

    