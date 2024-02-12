import threading
import random
from ctypes import *
from StatusClass import *
from ClientS7 import *
from Proceso import *
import socket
import time
# import signal


# class TimeoutException(Exception): 
#     pass

# def timeout_handler(signum, frame):
#     raise TimeoutException

# signal.signal(signal.SIGALRM, timeout_handler)



class FMC4030:

    # Ruta de driver para controlador FMC4030
    so_file = "/home/ubuntu/maqui/fmc4030-Drive/libFMC4030-Lib.so"
    fmc4030 = CDLL(so_file)    
    ms = machine_status() # Instancia de estado
    
    # Número del controlador, este número de identificación es único
    id = 1 
    ip = '192.168.0.30'
    port = 8088
    
    enable_status = False
    # Axis Comm Status
    Axis_Comm_Status = [0, 0, 0]
    
    # Actual Pos
    Axis_RealPos = [0, 0, 0]
    
    # Actual Speed
    Axis_RealSpeed = [0, 0, 0]
    
    # Home Status
    AxisX_Home = False
    AxisY_Home = False
    AxisZ_Home = False
    
    # Run Status
    AxisX_Run = False
    AxisY_Run = False
    AxisZ_Run = False
    
    # DI Status
    DIn0 = False  #Sensor de alambre
    DIn1 = False
    DIn2 = False
    DIn3 = False
    
    
    def __init__(self, controller_id: int, ipAddr: str, port: int):
        self.id = controller_id
        self.ip = ipAddr
        self.port = port
        self.connected = self.connect_Machine()
        self.listening_thread = threading.Thread(target=self.listening)
        self.listening_thread.daemon = True
        self.listening_thread.start()
        

    def __del__(self):
        self.disconnect_Machine()
        self.listening_thread.join()
    

    def connect_Machine(self):
        conn = 0
        try:
            conn = self.fmc4030.FMC4030_Open_Device(self.id, c_char_p(bytes(self.ip, 'utf-8')), self.port)
            print(self.ip)
            time.sleep(0.05)
            if conn == 0 :
                print("Connectado correctamente FMC: ", self.id)
                self.get_Status()
                print("Pos X: {:.2f} Y: {:.2f} Z: {:.2f}".format(self.ms.realPos[0], self.ms.realPos[1], self.ms.realPos[2]))
                print("Inputs: {}".format(self.ms.inputStatus[0]))  
                print("Outputs: {}".format(self.ms.outputStatus[0]))
                print("LimitN: {}".format(self.ms.limitNStatus[0]))
                print("LimitP: {}".format(self.ms.limitPStatus[0]))
                print("Mach RUN: {}".format(self.ms.machineRunStatus[0]))
                print("Axe Stat X: {} Y: {} Z: {}".format(self.ms.axisStatus[0], self.ms.axisStatus[1], self.ms.axisStatus[2]))
                print("Home Stat: {}".format(self.ms.homeStatus[0]))
            else: 
                print("Error de conexion FMC: ",self.id)
                raise ConnectionError(conn)
        except ConnectionError:
            print("Codiggo de error: ", conn)
            raise
        finally: return conn
        

    def disconnect_Machine(self):
        # Código para desconectarse de la máquina
        print("Desconectando : {}".format(self.fmc4030.FMC4030_Close_Device(self.id)))

    def get_Status(self):
        # Código para leer status de la máquina

        req_stat = [None]  # Mutable var so the function can store the result
        def func():
            req_stat[0] = self.fmc4030.FMC4030_Get_Machine_Status(self.id, pointer(self.ms))

        thread = threading.Thread(target=func)
        thread.start()

        # Wait for 2 seconds or until the thread finishes, whichever comes first
        thread.join(timeout=2)

        if thread.is_alive():
            print("Timeout: ", self.id)
            return -1
        
        time.sleep(0.03)
        #Din 01: XS001
        self.DIn0 = False if self.ms.inputStatus[0] & 0x0001 else True
        self.DIn1 = False if self.ms.inputStatus[0] & 0x0002 else True
        self.DIn2 = False if self.ms.inputStatus[0] & 0x0004 else True
        self.DIn3 = False if self.ms.inputStatus[0] & 0x0008 else True
        #Set Home Status
        self.AxisX_Home = True if self.ms.axisStatus[0] & 0x0800 else False
        self.AxisY_Home = True if self.ms.axisStatus[1] & 0x0800 else False
        self.AxisZ_Home = True if self.ms.axisStatus[2] & 0x0800 else False
        #Set RUN Status
        self.AxisX_Run = True if self.ms.axisStatus[0] & 0x0001 else False
        self.AxisY_Run = True if self.ms.axisStatus[1] & 0x0001 else False
        self.AxisZ_Run = True if self.ms.axisStatus[2] & 0x0001 else False
        #Set Actual Pos
        self.Axis_RealPos[0] = int(round(self.ms.realPos[0]))
        # print("Id: {} Act Pos: {}".format(self.id, self.AxisX_RealPos))
        self.Axis_RealPos[1] = int(round(self.ms.realPos[1]))
        # print("Id: {} Act Pos: {}".format(self.id, self.AxisY_RealPos))
        self.Axis_RealPos[2] = int(round(self.ms.realPos[2]))
        # print("Id: {} Act Pos: {}".format(self.id, self.AxisZ_RealPos))
        # print("Req Stat: ", req_stat)
        # print(self.id, req_stat)
        return req_stat[0]
        
    
    def get_Input(self, IO):
        # Código para leer estatus entradas digitales
        if IO==DIn0: print("Get Input: {}".format(self.fmc4030.FMC4030_Get_Input(self.id, IO, pointer(self.DIn0))))
        elif IO==DIn1: print("Get Input: {}".format(self.fmc4030.FMC4030_Get_Input(self.id, IO, pointer(self.DIn1))))
        elif IO==DIn2: print("Get Input: {}".format(self.fmc4030.FMC4030_Get_Input(self.id, IO, pointer(self.DIn2))))
        elif IO==DIn3: print("Get Input: {}".format(self.fmc4030.FMC4030_Get_Input(self.id, IO, pointer(self.DIn3))))
        
        
    def set_Output(self, IO=DOut0, Status=0):
        # Código para activar salida digital
        self.fmc4030.FMC4030_Set_Output(self.id, IO, Status)
        
    def get_AxisIsStop(self, Axis=axisX):
        # Código para leer si el eje esta detenido
        self.axisStop = False
        match Axis:
            case 0: 
                self.axisStop = True if self.fmc4030.FMC4030_Check_Axis_Is_Stop(self.id, axisX) == 1 else False
            case 1:
                self.axisStop = True if self.fmc4030.FMC4030_Check_Axis_Is_Stop(self.id, axisY) == 1 else False
            case 2:
                self.axisStop = True if self.fmc4030.FMC4030_Check_Axis_Is_Stop(self.id, axisZ) == 1 else False
            case 3:
                self.axisStop = True if (self.fmc4030.FMC4030_Check_Axis_Is_Stop(self.id, axisX) and 
                            self.fmc4030.FMC4030_Check_Axis_Is_Stop(self.id, axisY) and 
                            self.fmc4030.FMC4030_Check_Axis_Is_Stop(self.id, axisZ)) else False
        
        time.sleep(0.03)
        print("Axis is Stop: {} {}".format(Axis, self.axisStop))
        return self.axisStop
    
    def get_AxisCurrentPos(self, Axis=axisX):
        currentPos = c_float(0.0)
        self.Axis_Comm_Status[int(Axis.value)] = self.fmc4030.FMC4030_Get_Axis_Current_Pos(self.id, Axis, pointer(currentPos))
        self.Axis_RealPos[int(Axis.value)] = int(round(currentPos.value))
        # print("Call Current Pos: {}".format(self.Axis_Comm_Status[int(Axis.value)]))
        time.sleep(0.03)

    # ----------------------------------------------------- Get All Axis Position
    def get_AxisCurrentPosAll(self):
        """Get the current position of all axis
        Returns:
            tuple: (X, Y, Z)"""
        currentPos = (c_float * 3)()
        self.fmc4030.FMC4030_Get_Axis_Current_Pos_All(self.id, pointer(currentPos))
        print("Current Pos: ", currentPos[0], currentPos[1], currentPos[2])
        
        time.sleep(0.03)
        return currentPos[0], currentPos[1], currentPos[2]
    
    def get_AxisXYCurrentPos(self):
        currentPos = (c_float * 2)()
        axis_X = c_int(0)
        axis_Y = c_int(1)
        self.Axis_Comm_Status[int(axis_X.value)] = self.fmc4030.FMC4030_Get_Axis_Current_Pos(self.id, axis_X, pointer(currentPos[0]))
        self.Axis_Comm_Status[int(axis_Y.value)] = self.fmc4030.FMC4030_Get_Axis_Current_Pos(self.id, axis_Y, pointer(currentPos[1]))
        currentPos = (int(round(currentPos[0])), int(round(currentPos[1])))
        print("Current Pos: ", currentPos)
        time.sleep(0.03)
        return currentPos
    
    # Function to get home status of all axis
    def get_AxisHomeStatus(self):
        homeStatus = (c_int32 * 3)()
        self.fmc4030.FMC4030_Get_Axis_Home_Status(self.id, pointer(homeStatus))
        print("Home Status: ", homeStatus[0], homeStatus[1], homeStatus[2])
        time.sleep(0.03)
        return homeStatus[0], homeStatus[1], homeStatus[2]
    # -----------------------------------------------------
    
    def get_AxisCurrentSpeed(self, Axis=axisX):
        currentSpeed = c_float(0.0)
        self.Axis_Comm_Status[int(Axis.value)] = self.fmc4030.FMC4030_Get_Axis_Current_Speed(self.id, Axis, pointer(currentSpeed))
        self.Axis_RealSpeed[int(Axis.value)] = int(round(currentSpeed.value))
        print("Call Current Spd: {}".format(self.Axis_Comm_Status[int(Axis.value)]))
        time.sleep(0.03)
        
    def stop_Axis(self, Axis=axisX, Mode=1):
        print("Stop: {}".format(self.fmc4030.FMC4030_Stop_Single_Axis(self.id, Axis, Mode)))
        time.sleep(0.03)
    
    def stop_Run(self, id):
        print("Stop Run: {}".format(self.fmc4030.FMC4030_Stop_Run(id)))
        time.sleep(0.03)
    
    def home_Move(self, Axe=axisX, HomeSpeed=15, HomeAcc=200, HomeFall=15, HomeDir=2):
        # Código para poner a Home Eje
        print ("Home: {}".format(self.fmc4030.FMC4030_Home_Single_Axis(self.id, Axe, c_float(HomeSpeed), c_float(HomeAcc), c_float(HomeFall), HomeDir)))
        time.sleep(0.03)
    
    def jog_Move(self, Axe=axisX, AxePos=20, Speed=20, Acc=200, Dec=200):
        # Código para mover el Eje en modo JOG
        print ("Jog: {}".format(self.fmc4030.FMC4030_Jog_Single_Axis(self.id, Axe, c_float(AxePos), c_float(Speed), c_float(Acc), c_float(Dec), 1)))
        time.sleep(0.03)
    
    def abs_Move(self,Axe=axisX, AxePos=20, Speed=65, Acc=200, Dec=200):
        # Código para mover el Eje en modo Absoluto
        print ("Abs: {}".format(self.fmc4030.FMC4030_Jog_Single_Axis(self.id, Axe, c_float(AxePos), c_float(Speed), c_float(Acc), c_float(Dec), 2)))
        time.sleep(0.03)
    
    def rel_Move(self,Axe=axisX, AxePos=20, Speed=45, Acc=200, Dec=200):
        # Código para mover el Eje en modo Relativo
        print ("Rel: {}".format(self.fmc4030.FMC4030_Jog_Single_Axis(self.id, Axe, c_float(AxePos), c_float(Speed), c_float(Acc), c_float(Dec), 1)))
        time.sleep(0.03)
    
    def move_2Axis(self, Axis, EndX, EndY, Speed=30, Acc=200, Dec=200):
        # Código para mover 2 Ejes Sincronizados
        print ("2Axis: {}".format(self.fmc4030.FMC4030_Line_2Axis(self.id, Axis, c_float(EndX), c_float(EndY), c_float(Speed), c_float(Acc), c_float(Dec))))
        time.sleep(0.03)
    
    def move_3Axis(self, EndX, EndY, EndZ, Speed=10, Acc=200, Dec=200):
        # Código para mover 3 Ejes Sincronizados
        print ("3Axis: {}".format(self.fmc4030.FMC4030_Line_3Axis(self.id, 0, c_float(EndX), c_float(EndY), c_float(EndZ), c_float(Speed), c_float(Acc), c_float(Dec))))
        time.sleep(0.03)
    
    def move_Arc2Axis(self, Axis, EndX, EndY, CenterX, CenterY, Radius, Speed=10, Acc=10, Dec=10, Dir=1):
        # Código para mover 2 Ejes Sincronizados
        print ("Arc2Axis: {}".format(self.fmc4030.FMC4030_Arc_2Axis(self.id, Axis, c_float(EndX), c_float(EndY), c_float(CenterX), c_float(CenterY), c_float(Radius), c_float(Speed), c_float(Acc), c_float(Dec), Dir)))
        time.sleep(0.03)

    def listening(self):
        # self.enable_status = False
        # while True:
        pass
            # check if the machine is connected


            # self.get_AxisCurrentPos(axisX)    
            # if (self.ms.realPos[0] > 1500) and self.AxisX_Home and not self.enable_status : 
            #     self.set_Output(0,1)
            #     self.enable_status = True
            # elif (self.ms.realPos[0] <= 1500) and self.enable_status: 
            #     self.set_Output(0,0)
            #     self.enable_status = False
          
                
        
          