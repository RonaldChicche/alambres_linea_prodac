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
        self.radio_exterior = 101
        self.diametro_interior = 7
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
            if time.time() - start_time > 20:
                print(" ++++++++++++++++++ Stop Process: Tiempo de ejecucion excedido")
                self.plc_controller_right.stop_Run(id=self.plc_controller_right.id)
                self.plc_controller_left.stop_Run(id=self.plc_controller_left.id)
                # Move both drive on x axis to -50
                print("Moviendo a posicion de sefuridad -50")
                self.plc_controller_right.abs_Move(AxePos=-50)
                self.plc_controller_left.abs_Move(AxePos=-50)
                print(" ++++++++++++++++++ Terminando movimiento: Tiempo de ejecucion excedido")
                return -2

            # check if trigger is false
            if self.plc_parser.ctw_cam["TRIG_ESME"] == False:
                print(" ++++++++++++++++++ Stop Process: Trigger falso")
                self.plc_controller_right.stop_Run(id=self.plc_controller_right.id)
                self.plc_controller_left.stop_Run(id=self.plc_controller_left.id)
                # Move both drive on x axis to -50
                print("Moviendo a posicion de sefuridad -50")
                self.plc_controller_right.abs_Move(AxePos=-50)
                self.plc_controller_left.abs_Move(AxePos=-50)
                print(" ++++++++++++++++++ Terminando movimiento: Trigger falso")
                return -1
            
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
                    self.plc_controller_right.stop_Run(id=self.plc_controller_right.id)
                    # Move both drive on x axis to -50
                    print("Moviendo a posicion de sefuridad -50")
                    self.plc_controller_right.abs_Move(AxePos=-50)
                    print(" ++++++++++++++++++ Terminando movimiento: Trigger falso")
                    return -1
                
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
                    self.plc_controller_left.stop_Run(id=self.plc_controller_left.id)
                    # Move both drive on x axis to -50
                    print("Moviendo a posicion de sefuridad -50")
                    self.plc_controller_left.abs_Move(AxePos=-50)
                    print(" ++++++++++++++++++ Terminando movimiento: Trigger falso")
                    return -1
                
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
            #print(f"Left pos: {self.plc_controller_left.get_AxisCurrentPos(self.plc_controller_left.axisY)}")
            if self.plc_parser.ctw_cam["TRIG_ESME"] == False:
                # self.plc_parser.stw_cam["READY"] = True
                self.prev_state = False
                # print(f" ++++++++++++++++++ Reiniciando bit: {self.plc_parser.ctw_cam['TRIG_ESME']}, {self.prev_state}")


            # print axisXY pos from left
            # print(self.plc_controller_left.get_AxisXYCurrentPos())

            if self.plc_parser.ctw_cam["TRIG_ESME"] ^ self.prev_state:
                if self.prev_state == True:
                    continue

                print(f" ++++++++++++++++++ Iniciando rutina de control de esmeril: {self.plc_parser.ctw_cam['TRIG_ESME']}, {self.prev_state}")
                
                self.plc_parser.stw_cam["READY"] = False
                error = 0
                x_right, y_right, x_left, y_left = self.generar_trayectoria(self.diametro_interior/2, 
                                                                            self.radio_exterior, 12, 
                                                                            (-179, -177 + 2), (-202-3, -164 + 2))
                # verify if setpoints do not exceed the limits
                # for i in range(len(x_right)):
                #     if self.distancia_coor(x_right[i], y_right[i], x_left[i], y_left[i]) < 203:
                #         error = 4

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
                    # posicionar en -50 y -300 en el ejey respectivamente cada 1
                    self.move_2drives(-50, -50, -50, -300)

                    # Iniciar los pasos de la secuencia tomando de 3 en 3
                    for i in range(0, len(x_right), 3):
                        # ejecutar el primero en simultaneo y los otros 2 primero el derecho luego el izquierdo
                        res = self.move_2drives(x_right[i], y_right[i], x_left[i], y_left[i])
                        if res == -1 or res == -2:
                            break
                        time.sleep(0.2)
                        res = self.move_1drive(x_right[i + 1], y_right[i + 1], "right")
                        if res == -1 or res == -2:
                            break
                        time.sleep(0.2)
                        res = self.move_1drive(x_right[i + 2], y_right[i + 2], "right")
                        if res == -1 or res == -2:
                            break
                        time.sleep(0.2)
                        res = self.move_1drive(x_left[i + 1], y_left[i + 1], "left")
                        if res == -1 or res == -2:
                            break
                        time.sleep(0.2)
                        res = self.move_1drive(x_left[i + 2], y_left[i + 2], "left")
                        if res == -1 or res == -2:
                            break

                    self.plc_controller_right.abs_Move(AxePos=-50)
                    self.plc_controller_left.abs_Move(AxePos=-50)

                    self.plc_parser.stw_cam["BUSY"] = False
                    self.plc_parser.stw_cam["ERROR"] = False
                    
                    self.plc_parser.stw_cam["READY"] = True
                self.prev_state = self.plc_parser.ctw_cam["TRIG_ESME"]
                print(f" ++++++++++++++++++ Terminando rutina de control de esmeril: {self.plc_parser.ctw_cam['TRIG_ESME']}, {self.prev_state}")
        


    def generar_trayectoria(self, radio:float, radio_esmeril:float, num_lados:int, right_center:tuple, left_center:tuple):
        """ Genera una trayectoria de un poligono regular con circunferencia inscrita
        Args:
            radio (float): radio del poligono
            radio_esmeril (float): radio de la circunferencia inscrita
            num_lados (int): numero de lados del poligono, siempre par y mayor a 2
            right_center (tuple): centro del lado derecho
            left_center (tuple): centro del lado izquierdo
        Returns:
            lists: (x_right, y_right, x_left, y_left)"""
        # Print characteristics
        print(f"Radio: {radio}, Radio Esmeril: {radio_esmeril}, Num Lados: {num_lados}, Right Center: {right_center}, Left Center: {left_center}")
        # raise error if num_lados is less than 3 an uneven
        if num_lados < 3 or num_lados % 2 != 0:
            raise ValueError("num_lados must be an even number greater than 2")
        # Definir angulo de inicio del lado derecho 
        angulo_init = np.pi / 2
        # Definir longitud de trayectoria
        path = 70
        
        # Definir limites
        x_limit = -215
        y_limit = -330
        # calcular cantidad de angulos segun el numero de lados
        angulos = np.linspace(angulo_init, angulo_init + 2 * np.pi, num_lados, endpoint=False)
        # Calcular los puntos (vértices del polígono excrito al radio) considerando el radio_esmeril
        x = (radio_esmeril + radio) * np.cos(angulos)
        y = (radio_esmeril + radio) * np.sin(angulos)

        # generar lineas tangentes a la circunferencia de radio esmeril que pasen por los puntos x, y
        points = []
        for i in range(num_lados):
            # Calcular la pendiente de la recta tangente
            m = np.arctan2(y[i],x[i]) + np.pi/2
            # Calcular el 2 puntos de la recta tangente con la circunferencia de radio esmeril que pasa por y[i], x[i]
            x1 = x[i] + path/2 * np.cos(m)
            y1 = y[i] + path/2 * np.sin(m)
            x2 = x[i] - path/2 * np.cos(m)
            y2 = y[i] - path/2 * np.sin(m)
            # add them to ppoints as tuple (x1, y1) (x2, y2)
            points.append((x1, y1))
            points.append((x2, y2))
            points.append((x1, y1))
            
        # divide them in left and right from the center
        points_right = points[:len(points)//2]
        points_left = points[len(points)//2:]
        # turn them  into numpy arrays
        points_right = np.array(points_right)
        points_left = np.array(points_left)
        # translate them to the center
        points_right = (points_right.round() + right_center).astype(int)
        points_left = (points_left.round() + left_center).astype(int)
        # invert points_right by the x axis taking right_center x as reference to reflect
        points_right[:, 0] = 2 * right_center[0] - points_right[:, 0]
        # recorre points right and left de 3 en tres
        for i in range(0, len(points_right), 3):
            for j in range(2):
                if i + j < len(points_right):
                    # apply x limit
                    if points_right[i + j][0] < x_limit:
                        points_right[i + j][0] = x_limit
                    if points_left[i + j][0] < x_limit:
                        points_left[i + j][0] = x_limit
        # split points_right and points_left into x, y right and left
        x, y = zip(*points_right)
        x_right = list(x)
        y_right = list(y)
        x, y = zip(*points_left)
        x_left = list(x)
        y_left = list(y)

        return x_right, y_right, x_left, y_left
