import numpy as np
import threading
import time

class EsmerilWebApp:
    def __init__(self):
        self.run = True
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
        # define left and right drives
        self.plc_controller_right = None

    def __del__(self):
        print(" ++++++++++++++++++ Terminando hilo de control de esmeril")
        self.run = False
        if self.thread_plc is not None:
            self.thread_plc.join()

    def start_plc_thread(self, plc_parser):
        print(" ++++++++++++++++++ Iniciando hilo de control de esmeril")
        self.plc_parser = plc_parser
        self.thread_plc = threading.Thread(target=self.plc_control)
        self.thread_plc.start()

    def move_2drives(self, x, y, x1, y1):
        start_time = time.time()
        print(f" -> +++++++++ Objetivo: \n->\t Right: {x}, {y} ||\t Left: {x1}, {y1} ")
        self.plc_controller_right.move_2Axis(3, x, y)
        self.plc_controller_left.move_2Axis(3, x1, y1)
        while True:
            # check if has passed 10 seconds
            if time.time() - start_time > 15:
                print(" ++++++++++++++++++ Stop Process: Tiempo de ejecucion excedido")
                self.plc_controller_right.stop()
                self.plc_controller_left.stop()
                # Move both drive on x axis to -50
                print("Moviendo a posicion de sefuridad -50")
                self.plc_controller_right.absMove(AxePos=-50)
                self.plc_controller_left.absMove(AxePos=-50)
                print(" ++++++++++++++++++ Terminando movimiento: Tiempo de ejecucion excedido")
                return 0

            # check if trigger is false
            if self.plc_parser.ctw_cam["TRIG_ESME"] == False:
                print(" ++++++++++++++++++ Stop Process: Trigger falso")
                self.plc_controller_right.stop()
                self.plc_controller_left.stop()
                # Move both drive on x axis to -50
                print("Moviendo a posicion de sefuridad -50")
                self.plc_controller_right.absMove(AxePos=-50)
                self.plc_controller_left.absMove(AxePos=-50)
                print(" ++++++++++++++++++ Terminando movimiento: Trigger falso")
                return 0
            
            rpos_x, rpos_y = self.plc_controller_right.get_AxisXYCurrentPos()
            lpos_x, lpos_y = self.plc_controller_left.get_AxisXYCurrentPos()
            if abs(rpos_x - x) < 0.1 and abs(rpos_y - y) < 0.1 and abs(lpos_x - x1) < 0.1 and abs(lpos_y - y1) < 0.1:
                print(" ++++++++++++++++++ Terminando movimiento")
                return 0
            else:
                print(f" -> +++++++++ Right: {rpos_x}, {rpos_y} || Left: {lpos_x}, {lpos_y}")

            time.sleep(0.1)
    
    def move_1drive(self, x, y, side):
        if side == "right":
            print(f" -> +++++++++ Objetivo: \n->\t Right: {x}, {y} ")
            self.plc_controller_right.move_2Axis(3, x, y)
            while True:
                # check if trigger is false
                if self.plc_parser.ctw_cam["TRIG_ESME"] == False:
                    print(" ++++++++++++++++++ Stop Process: Trigger falso")
                    self.plc_controller_right.stop()
                    # Move both drive on x axis to -50
                    print("Moviendo a posicion de sefuridad -50")
                    self.plc_controller_right.absMove(AxePos=-50)
                    print(" ++++++++++++++++++ Terminando movimiento: Trigger falso")
                    return 0
                
                rpos_x, rpos_y = self.plc_controller_right.get_AxisXYCurrentPos()
                if abs(rpos_x - x) < 0.1 and abs(rpos_y - y) < 0.1:
                    print(" ++++++++++++++++++ Terminando movimiento")
                    return 0
                else:
                    print(f" -> +++++++++ Right: {rpos_x}, {rpos_y}")
                time.sleep(0.1)
        elif side == "left":
            print(f" -> +++++++++ Objetivo: \n->\t Left: {x}, {y} ")
            self.plc_controller_left.move_2Axis(3, x, y)
            while True:
                # check if trigger is false
                if self.plc_parser.ctw_cam["TRIG_ESME"] == False:
                    print(" ++++++++++++++++++ Stop Process: Trigger falso")
                    self.plc_controller_left.stop()
                    # Move both drive on x axis to -50
                    print("Moviendo a posicion de sefuridad -50")
                    self.plc_controller_left.absMove(AxePos=-50)
                    print(" ++++++++++++++++++ Terminando movimiento: Trigger falso")
                    return 0
                
                lpos_x, lpos_y = self.plc_controller_left.get_AxisXYCurrentPos()
                if abs(lpos_x - x) < 0.1 and abs(lpos_y - y) < 0.1:
                    print(" ++++++++++++++++++ Terminando movimiento")
                    return 0
                else:
                    print(f" -> +++++++++ Left: {lpos_x}, {lpos_y}")
                time.sleep(0.1)

    def distancia_coor(self, x1, y1, x2, y2):
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
        while self.run: 
            # print(f"Esperando trigger --------------------------------------------------------------------------{self.plc_parser.ctw_cam}")
            # # Rutina de ejecucion
            if self.plc_parser.ctw_cam["TRIG_ESME"] == False:
                # self.plc_parser.stw_cam["READY"] = True
                self.prev_state = False

            # print axisXY pos from left
            # print(self.plc_controller_left.get_AxisXYCurrentPos())

            if self.plc_parser.ctw_cam["TRIG_ESME"] ^ self.prev_state:
                if self.prev_state == True:
                    continue
                
                self.plc_parser.stw_cam["READY"] = False
                x_right, y_right, x_left, y_left, error = self.generar_trayectoria(self.num_toques, self.radio_exterior, self.diametro_interior, self.centro_x, self.centro_y, self.angulo_inicio, self.angulo_fin)
                # verify if setpoints do not exceed the limits
                for i in range(len(x_right)):
                    if self.distancia_coor(x_right[i], y_right[i], x_left[i], y_left[i]) < 203:
                        error = 4

                # # verify if drives are home -----------------------------
                # if self.plc_controller_right.get_AxisHomeStatus(3) == 0 or self.plc_controller_left.get_AxisHomeStatus(3) == 0:
                #     error = 2
                
                if error == 1:
                    self.plc_parser.stw_cam["ERROR"] = True
                    self.plc_parser.stw_cam["READY"] = False
                    print("Error 1: radio_exterior < radio_interior + 101.6")
                elif error == 2:
                    self.plc_parser.stw_cam["ERROR"] = True
                    self.plc_parser.stw_cam["READY"] = False
                    print("Error 2: no home drives")
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
                    # ---------------------------------------------------
                    # posicionar ambos en el de la derecha en -50, -50 y el de la izquierda en -50, -300
                    self.move_2drives(-50, -50, -50, -300)

                    # Iniciar los pasos de la secuencia tomando de 3 en 3
                    for i in range(0, len(x_right), 3):
                        # ejecutar el primero en simultaneo y los otros 2 primero el derecho luego el izquierdo
                        self.move_2drives(x_right[i], y_right[i], x_left[i], y_left[i])
                        time.sleep(0.2)
                        self.move_1drive(x_right[i + 1], y_right[i + 1], "right")
                        time.sleep(0.2)
                        self.move_1drive(x_right[i + 2], y_right[i + 2], "right")
                        time.sleep(0.2)
                        self.move_1drive(x_left[i + 1], y_left[i + 1], "left")
                        time.sleep(0.2)
                        self.move_1drive(x_left[i + 2], y_left[i + 2], "left")

                    self.plc_parser.stw_cam["BUSY"] = False
                    self.plc_parser.stw_cam["ERROR"] = False
                    
                    self.plc_parser.stw_cam["READY"] = True
                self.prev_state = self.plc_parser.ctw_cam["TRIG_ESME"]
        


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