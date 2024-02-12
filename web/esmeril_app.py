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
        print(f" -> +++++++++ Left: {x1}, {y1} Right: {x}, {y}")
        self.plc_controller_right.move_2Axis(3, x, y)
        # self.plc_controller_left.move_2Axis(3, x1, y1)
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


            if self.plc_parser.ctw_cam["TRIG_ESME"] ^ self.prev_state:
                if self.prev_state == True:
                    continue
                print(f" ++++++++++++++++++ Iniciando rutina de control de esmeril: {self.plc_parser.ctw_cam['TRIG_ESME']}, {self.prev_state}")
                
                self.plc_parser.stw_cam["READY"] = False
                x_right, y_right, x_left, y_left = self.generar_trayectoria(self.diametro_interior/2, 
                                                                            self.radio_exterior, 6, 
                                                                            (-179, -177 + 2), (-202-3, -164 + 2))
                # verify if setpoints do not exceed the limits
                # for i in range(len(x_right)):
                #     if self.distancia_coor(x_right[i], y_right[i], x_left[i], y_left[i]) < 203:
                #         error = 4
                error = 0
                
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
                    # self.move_1drive(x_right.pop(0), y_right.pop(0), "right")

                    # self.move_2drives(x_left.pop(i), y_left.pop(i), x_right.pop(i), y_right.pop(i))
                    # self.move_1drive(x_right.pop(0), y_right.pop(0), "right")

                    # for i in range(0, len(x_right), 2):
                    #     for j in range(2):
                    #         if i + j < len(x_right):
                    #             self.move_2drives(x_left[i + j], y_left[i + j], x_right[i + j], y_right[i + j])
                    #             time.sleep(0.1)
                    #     time.sleep(1)

                    # self.move_1drive(x_left[-1], y_left[-1], "left")
                    # --------------------------------------------------- last routine
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

                    # execute the routine taking the first 3 from right the the first 3 from left and so on
                    # execute the first one of both of them
                    # self.plc_controller_right.move_2Axis(axis, -70, -170)
                    # time.sleep(0.5)
                    # self.plc_controller_left.move_2Axis(axis, -70, -167)
                    # time.sleep(5)
                    print(len(x_right))
                    for i in range(0, len(x_right), 3):
                        self.plc_controller_right.move_2Axis(axis, x_right[i], y_right[i], Speed=40)
                        print(f" -> Right {i}: {x_right[i]}, {y_right[i]}")
                        time.sleep(0.2)
                        self.plc_controller_left.move_2Axis(axis, x_left[i], y_left[i], Speed=40)
                        print(f" -> Left {i}: {x_left[i]}, {y_left[i]}")
                        if i == 0:
                            time.sleep(4)
                        else:
                            time.sleep(5.5)

                        #primer paso derecho
                        self.plc_controller_right.move_2Axis(axis, x_right[i+1], y_right[i+1], Speed=40)
                        print(f" -> Right {i+1}: {x_right[i+1]}, {y_right[i+1]}")
                        if i == 0:
                            time.sleep(4)
                        else:
                            time.sleep(6.5)
                        self.plc_controller_right.move_2Axis(axis, x_right[i+2], y_right[i+2], Speed=40)
                        print(f" -> Right {i+2}: {x_right[i+2]}, {y_right[i+2]}")
                        time.sleep(2)
                        self.plc_controller_left.move_2Axis(axis, x_left[i+1], y_left[i+1], Speed=40)
                        print(f" -> Left {i+1}: {x_left[i+1]}, {y_left[i+1]}")
                        if i == 0:
                            time.sleep(4)
                        else:
                            time.sleep(6.5)
                        self.plc_controller_left.move_2Axis(axis, x_left[i+2], y_left[i+2], Speed=40)
                        print(f" -> Left {i+2}: {x_left[i+2]}, {y_left[i+2]}")
                        if i == 0:
                            time.sleep(4)
                        else:
                            time.sleep(6.5)


                        # for j in range(3):
                        #     if i + j < len(x_right):
                        #         # exceute the movement from the right only
                        #         self.plc_controller_right.move_2Axis(axis, x_right[i + j], y_right[i + j])
                        #         print(f" -> Right: {x_right[i + j]}, {y_right[i + j]}")
                        #         time.sleep(5)
                        # for j in range(3):
                        #     if i + j < len(x_left):
                        #         # exceute the movement from the left only
                        #         self.plc_controller_left.move_2Axis(axis, x_left[i + j], y_left[i + j])
                        #         print(f" -> Left: {x_left[i + j]}, {y_left[i + j]}")
                        #         time.sleep(7)
                        # time.sleep(0.5)

                    # excute the last 2
                    # self.plc_controller_right.move_2Axis(axis, x_right.pop(-2), y_right.pop(-2))
                    # time.sleep(5)
                    # self.plc_controller_right.move_2Axis(axis, x_right.pop(-1), y_right.pop(-1))
                    # time.sleep(0.5)
                    # self.plc_controller_left.move_2Axis(axis, x_left.pop(-2), y_left.pop(-2))
                    # time.sleep(5)
                    # self.plc_controller_left.move_2Axis(axis, x_left.pop(-1), y_left.pop(-1))

                    


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
        # raise error if num_lados is less than 3 an uneven
        if num_lados < 3 or num_lados % 2 != 0:
            raise ValueError("num_lados must be an even number greater than 2")
        # Definir angulo de inicio del lado derecho 
        angulo_init = np.pi / 2
        # Definir longitud de trayectoria
        path = 150
        
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
