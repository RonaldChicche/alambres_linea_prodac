import numpy as np
import threading
import time

class EsmerilWebApp:
    def __init__(self):
        self.prev_state = False
        self.plc_controller_right = None
        self.plc_controller_left = None
        self.plc_parser = None
        self.thread_plc = None
        # variables 
        self.num_toques = 6
        self.radio_exterior = 130
        self.diametro_interior = 10
        self.centro_x = -192
        self.centro_y = -160
        self.angulo_inicio = 90
        self.angulo_fin = 270
        self.dt = 0.5

    def __del__(self):
        print(" ++++++++++++++++++ Terminando hilo de control de esmeril")
        self.thread_plc.join()

    def start_plc_thread(self, plc_parser):
        print(" ++++++++++++++++++ Iniciando hilo de control de esmeril")
        self.plc_parser = plc_parser
        self.thread_plc = threading.Thread(target=self.plc_control)
        self.thread_plc.start()

    def move_2drives(self, x, y, x1, y1):
        print(f" -> +++++++++ Left: {x1}, {y1} Right: {x}, {y}")
        self.plc_controller_right.move_2Axis(3, x, y)
        self.plc_controller_left.move_2Axis(3, x1, y1)
        while True:
            right_pos_x = round(self.plc_controller_right.ms.realPos[0], 2)
            right_pos_y = round(self.plc_controller_right.ms.realPos[1], 2)
            left_pos_x = round(self.plc_controller_left.ms.realPos[0], 2)
            left_pos_y = round(self.plc_controller_left.ms.realPos[1], 2)
            if abs(right_pos_x - x) < 0.1 and abs(right_pos_y - y) < 0.1 and abs(left_pos_x - x1) < 0.1 and abs(left_pos_y - y1) < 0.1:
                print(f" ++++++++++++++++++ Terminando movimiento - Right : {right_pos_x}, {right_pos_y} - Left : {left_pos_x}, {left_pos_y}")
                return 0
            else:
                print(f" -> +++++++++ Left: {left_pos_x}, {left_pos_y} Right: {right_pos_x}, {right_pos_y}")
            time.sleep(0.1)
        # self.move_1drive(x1, y1, "left")
        # self.move_1drive(x, y, "right")
    
    def move_1drive(self, x, y, side):
        if side == "right":
            print(f" Right: {x}, {y}")
            self.plc_controller_right.move_2Axis(3, x, y)
            while True:
                right_pos_x = self.plc_controller_right.Axis_RealPos[0]
                right_pos_y = self.plc_controller_right.Axis_RealPos[1]
                if abs(right_pos_x - x) < 0.1 and abs(right_pos_y - y) < 0.1:
                    print(" ++++++++++++++++++ Terminando movimiento")
                    return 0
                else:
                    print(f" -> +++++++++ Right: {right_pos_x}, {right_pos_y}")
                time.sleep(0.1)
        elif side == "left":
            print(f" Left: {x}, {y}")
            self.plc_controller_left.move_2Axis(3, x, y)
            while True:
                left_pos_x = self.plc_controller_left.Axis_RealPos[0]
                left_pos_y = self.plc_controller_left.Axis_RealPos[1]
                if abs(left_pos_x - x) < 0.1 and abs(left_pos_y - y) < 0.1:
                    print(" ++++++++++++++++++ Terminando movimiento")
                    return 0
                else:
                    print(f" -> +++++++++ Left: {left_pos_x}, {left_pos_y}")
                time.sleep(0.1)

    def distancia_coor(x1, y1, x2, y2):
        """ x1 y y1 son las coordenadas del punto en el sistema principal
            x2 y y2 son las coordenadas del punto en el sistema trasladado
        """
        # traslacion de coordenadas x2 y y2
        x2 = -x2 - 387 
        y2 =  y2 - 0
        # calculo de la distancia
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def plc_control(self):
        
        # # Test
        self.plc_controller_right = self.plc_parser.CtrlFMC[3]
        self.plc_controller_left = self.plc_parser.CtrlFMC[2]

        self.prev_state = False
        while True: 
            # print(f"Esperando trigger --------------------------------------------------------------------------{self.plc_parser.ctw_cam}")
            # # Rutina de ejecucion
            
            # self.move_1drive(0, 0, side="left")
            # time.sleep(1)
            # self.move_1drive(-20, -100, side="left")
            # time.sleep(1)
            
            # self.move_1drive(0, -100, "right")

            if self.plc_parser.ctw_cam["TRIG_ESME"] == False:
                self.plc_parser.stw_cam["READY"] = True
                self.prev_state = False


            if self.plc_parser.ctw_cam["TRIG_ESME"] ^ self.prev_state:
                # self.num_toques = self.plc_parser.ctw_plc["NUM_TOQUES"]
                # self.radio_exterior = self.plc_parser.ctw_plc["RADIO_EXTERIOR"]
                # self.diametro_interior = self.plc_parser.ctw_plc["DIAMETRO_INTERIOR"]
                # self.centro_x = self.plc_parser.ctw_plc["CENTRO_X"]
                # self.centro_y = self.plc_parser.ctw_plc["CENTRO_Y"]
                # self.angulo_inicio = self.plc_parser.ctw_plc["ANGULO_INICIO"]
                # self.angulo_fin = self.plc_parser.ctw_plc["ANGULO_FIN"] 
                # self.dt = self.plc_parser.ctw_plc["DT"]
                
                self.plc_parser.stw_cam["READY"] = False
                x_right, y_right, x_left, y_left, error = self.generar_trayectoria(self.num_toques, self.radio_exterior, self.diametro_interior, self.centro_x, self.centro_y, self.angulo_inicio, self.angulo_fin)
                # verify if setpoints do not exceed the limits
                for i in range(len(x_right)):
                    if self.distancia_coor(x_right[i], y_right[i], x_left[i], y_left[i]) < 203:
                        error = 4
                
                if error == 1:
                    self.plc_parser.stw_cam["ERROR"] = True
                    self.plc_parser.stw_cam["READY"] = False
                    print("Error 1: radio_exterior < radio_interior + 101.6")
                elif error == 2:
                    self.plc_parser.stw_cam["ERROR"] = True
                    self.plc_parser.stw_cam["READY"] = False
                    print("Error 2: num_toques < 3")
                elif error == 3:
                    self.plc_parser.stw_cam["ERROR"] = True
                    self.plc_parser.stw_cam["READY"] = False
                    print("Error 3: centro de la estrella fuera de rango ")
                elif error == 4:
                    self.plc_parser.stw_cam["ERROR"] = True
                    self.plc_parser.stw_cam["READY"] = False
                    print("Error 4: setpoints fuera de rango ")                
                else:
                    self.plc_parser.stw_cam["BUSY"] = True
                    self.plc_controller_right = self.plc_parser.CtrlFMC[3]
                    self.plc_controller_left = self.plc_parser.CtrlFMC[2]
                    
                    # Rutina de ejecucion con self.move_2drives
                    axis = 3
                    i = 0
                    self.move_2drives(x_left.pop(i), y_left.pop(i), x_right.pop(i), y_right.pop(i))
                    self.move_1drive(x_right.pop(0), y_right.pop(0), "right")

                    for i in range(0, len(x_right), 2):
                        for j in range(2):
                            if i + j < len(x_right):
                                self.move_2drives(x_left[i + j], y_left[i + j], x_right[i + j], y_right[i + j])
                                time.sleep(0.1)
                        time.sleep(1)

                    self.move_1drive(x_left[-1], y_left[-1], "left")
                    # ---------------------------------------------------
                    # self.plc_controller_left.move_2Axis(axis, x_left.pop(i), y_left.pop(i))
                    # self.plc_controller_right.move_2Axis(axis, x_right.pop(i), y_right.pop(i))
                    # time.sleep(2)
                    # self.plc_controller_right.move_2Axis(axis, x_right.pop(0), y_right.pop(0))
                    # time.sleep(2)
                    # for i in range(0, len(x_right), 2):
                    #     for j in range(2):
                    #         if i + j < len(x_right):
                    #             self.plc_controller_left.move_2Axis(axis, x_left[i + j], y_left[i + j])
                    #             time.sleep(0.1)
                    #             self.plc_controller_right.move_2Axis(axis, x_right[i + j], y_right[i + j])
                    #             time.sleep(4)  
                    #     time.sleep(2)

                    # self.plc_controller_left.move_2Axis(axis, x_left[-1], y_left[-1])

                    self.plc_parser.stw_cam["BUSY"] = False
                    self.plc_parser.stw_cam["ERROR"] = False
                    
                    # self.plc_parser.stw_cam["READY"] = True
                self.prev_state = self.plc_parser.ctw_plc["TRIG_ESME"]
        


    def generar_trayectoria(self, num_toques, radio_exterior, diametro_interior, centro_x, centro_y, angulo_inicio, angulo_fin):
        """Genera una lista de puntos para una trayectoria estrella de N puntas con radio exterior y radio interior
            Error 1: radio_exterior < radio_interior + 101.6
            Error 2: num_toques < 3
            Error 3: centro de la estrella fuera de rango """
            
        angulo_inicio = np.deg2rad(angulo_inicio)
        angulo_fin = np.deg2rad(angulo_fin)

        # Transforma radios
        radio_interior = diametro_interior / 2 + 100.6
        if radio_exterior < radio_interior:
            return None, None, None, None, 1
        elif num_toques < 3:
            return None, None, None, None, 2
        # Calcula los ángulos para los vértices exteriores e interiores de la estrella
        angulos_right = np.linspace(angulo_inicio, angulo_fin, num_toques + 1)
        angulos_left = angulos_right + np.pi

        # Calcula las coordenadas de los puntos exteriores e interiores de la estrella
        centro_x = -176
        centro_y = -176
        x_exterior = -radio_exterior * np.cos(angulos_right) + centro_x
        y_exterior = radio_exterior * np.sin(angulos_right) + centro_y 
        x_interior = -radio_interior * np.cos(angulos_right) + centro_x 
        y_interior = radio_interior * np.sin(angulos_right) + centro_y

        # Combina las coordenadas para formar la estrella
        x_right = [int(item) for pair in zip(x_exterior, x_interior) for item in pair]
        y_right = [int(item) for pair in zip(y_exterior, y_interior) for item in pair]

        # Calcula las coordenadas de los puntos exteriores e interiores de la estrella
        centro_x = -213
        centro_y = -179
        x_exterior = radio_exterior * np.cos(angulos_left) + centro_x 
        y_exterior = radio_exterior * np.sin(angulos_left) + centro_y 
        x_interior = radio_interior * np.cos(angulos_left) + centro_x 
        y_interior = radio_interior * np.sin(angulos_left) + centro_y 

        # Combina las coordenadas para formar la estrella
        x_left = [int(item) for pair in zip(x_exterior, x_interior) for item in pair]
        y_left = [int(item) for pair in zip(y_exterior, y_interior) for item in pair]

        return x_right[:-1], y_right[:-1], x_left[:-1], y_left[:-1], 0