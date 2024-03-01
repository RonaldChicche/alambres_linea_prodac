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
        self.diametro_interior = 8
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
                                                                            (-207, -179+5-1), (-225-3, -167-5))
                                                                            
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
                    for i in range(0, len(x_right), 4):
                        # ejecutar el primero en simultaneo y los otros 2 primero el derecho luego el izquierdo
                        
                        res = self.move_1drive(x_right[i], y_right[i], "right")
                        if res == -1 or res == -2:
                            break
                        time.sleep(0.2)
                        
                        res = self.move_1drive(x_right[i + 1], y_right[i + 1], "right")
                        if res == -1 or res == -2:
                            break
                        time.sleep(0.2)

                        if i+2 < len(x_right):
                            res = self.move_1drive(x_right[i + 2], y_right[i + 2], "right")
                            if res == -1 or res == -2:
                                break
                            time.sleep(0.2)
                        else:
                            self.plc_controller_right.abs_Move(AxePos=-50)

                        # res = self.move_1drive(x_left[i], y_left[i], "left")
                        if i+3 < len(x_right) and i != 0:
                            res = self.move_2drives(x_right[i+3], y_right[i+3], x_left[i], y_left[i])
                        else:
                            self.plc_controller_right.abs_Move(AxePos=-50)
                            res = self.move_1drive(x_left[i], y_left[i], "left")
                        if res == -1 or res == -2:
                            break
                        time.sleep(0.2)

                        
                        res = self.move_1drive(x_left[i + 1], y_left[i + 1], "left")
                        if res == -1 or res == -2:
                            break
                        time.sleep(0.2)

                        if i+2 < len(x_left):
                            res = self.move_1drive(x_left[i + 2], y_left[i + 2], "left")
                            if res == -1 or res == -2:
                                break
                            time.sleep(0.2)
                        else:
                            self.plc_controller_left.abs_Move(AxePos=-50)


                        if i+3 < len(x_left):
                            res = self.move_1drive(x_left[i+3], y_left[i+3], "left")
                            if res == -1 or res == -2:
                                break
                        else:
                            self.plc_controller_left.abs_Move(AxePos=-50)

                    self.plc_controller_right.abs_Move(AxePos=-50)
                    self.plc_controller_left.abs_Move(AxePos=-50)

                    self.plc_parser.stw_cam["BUSY"] = False
                    self.plc_parser.stw_cam["ERROR"] = False
                    
                    self.plc_parser.stw_cam["READY"] = True
                self.prev_state = self.plc_parser.ctw_cam["TRIG_ESME"]
                print(f" ++++++++++++++++++ Terminando rutina de control de esmeril: {self.plc_parser.ctw_cam['TRIG_ESME']}, {self.prev_state}")
        

    def generar_trayectoria(self, radio_interior, radio_esme, n, right_center, left_center):
        # Verificar si n es par
        if n % 2 != 0:
            raise ValueError("n debe ser un número par")    
        # Ángulo entre vértices
        angulo = 2 * np.pi / n
        angulo_interior = 2 * np.pi / n
        # Radio es la hipotenusa del triángulo rectángulo formado por la mitad de un lado del polígono y el radio
        radio = (radio_esme + radio_interior) / np.cos(angulo_interior / 2)
        
        # Coordenadas de los vértices del polígono
        x = []
        y = []
        for i in range(int(n/2) + 2):
            print(f"Side {i} from n/2={int(n/2)}, angle: {np.degrees(i * angulo + np.pi/2)}")
            x_i = np.cos(i * angulo + np.pi/2) * radio
            y_i = np.sin(i * angulo + np.pi/2) * radio
            x.append(x_i)
            y.append(y_i)

        # Cada 2 elementos agregamos un punto en la lista despues de estos, la coordenada es en medio de los 2 previos con radio esme + 10
        x_paso = []
        y_paso = []
        for i in range(0, len(x) + 1 , 2):
            x_i = (radio + 20) * np.cos(i/2 * angulo + angulo/2 + np.pi / 2) 
            y_i = (radio + 20) * np.sin(i/2 * angulo + angulo/2 + np.pi / 2)
            x_paso.append(x_i)
            y_paso.append(y_i)
        
        # Formamos la rayectoria tomando 2 puntos de x y y y 1 de x_paso y y_paso
        x_right = []
        y_right = []
        for i in range(0, 2 * len(x_paso) + 2, 2):
            x_right.append(x[i//2])
            y_right.append(y[i//2])
            x_right.append(x[i//2 + 1])
            y_right.append(y[i//2 + 1])
            x_right.append(x[i//2])
            y_right.append(y[i//2])
            if i <= len(y_paso) + 4:
                x_right.append(x_paso[int(i/2)])
                y_right.append(y_paso[int(i/2)])

        
        # Convierte las listas x e y en arreglos de NumPy
        x_right = np.array(x_right) * -1
        y_right = np.array(y_right)
        #  Genera x_left y y_left reflejando x_right y y_right por el eje x
        x_left = np.copy(x_right)
        y_left = np.copy(-y_right)

        # Transladar el polígono al centro right_center
        x_right += right_center[0]
        y_right += right_center[1]
        # Transladar el polígono al centro left_center
        x_left += left_center[0]
        y_left += left_center[1]
            
        return x_right, y_right, x_left, y_left
