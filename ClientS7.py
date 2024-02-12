import threading
# import keyboard
import random
import requests
import snap7
import signal
import time
from snap7 import util
from  StatusClass import *
from ControllerClass import *
from ClientHttp import *


class PLCDataParser(HTTPDataSender):
    
    id = 0
    plc_ip = '192.168.90.10'
    rack = 0
    slot = 1
    idCtrl = 1
    conn_diag = 0
    
    ctw_mask = { "AxisX": 0xFFFF, "AxisY": 0xFFFF, "AxisZ": 0xFFFF, "2Axis_XY": 0xFFFF, "3Axis_XYZ": 0xFFFF, "ARC_XY": 0xFFFF}
    
    data_struc = {
        "SYSTEM":{
            "LINK":     False,
            "STATUS":   0,
            "INPUTS":   0,
            "OUTPUTS":  0
        },
        "AxisX":{
            "STW":      0,
            "CTW":      0,
            "SP_POS":   0,
            "SP_VEL":   0,
            "SP_HVEL":  0,
            "PV_POS":   0,
            "PV_VEL":   0,
            "ACC":      0,
            "DEC":      0,
            "HACC":     0,
            "DIR":      0,
            "FALL":     0
            },
        "AxisY":{
            "STW":      0,
            "CTW":      0,
            "SP_POS":   0,
            "SP_VEL":   0,
            "SP_HVEL":  0,
            "PV_POS":   0,
            "PV_VEL":   0,
            "ACC":      0,
            "DEC":      0,
            "HACC":     0,
            "DIR":      0,
            "FALL":     0
            },
        "AxisZ":{
            "STW":      0,
            "CTW":      0,
            "SP_POS":   0,
            "SP_VEL":   0,
            "SP_HVEL":  0,
            "PV_POS":   0,
            "PV_VEL":   0,
            "ACC":      0,
            "DEC":      0,
            "HACC":     0,
            "DIR":      0,
            "FALL":     0
            },
        "2Axis_XY":{
            "CTW":       0,
            "SP_POSX":   0,
            "SP_POSY":   0,
            "SP_POSZ":   0,
            "SP_VEL":    0,
            "ACC":       0,
            "DEC":      0
            },
        "3Axis_XYZ":{
            "CTW":      0,
            "SP_POSX":   0,
            "SP_POSY":   0,
            "SP_POSZ":   0,
            "SP_VEL":  0,
            "ACC":      0,
            "DEC":      0
            },
        "ARC_XY":{
            "CTW":      0,
            "SP_POSX":   0.0,
            "SP_POSY":   0.0,
            "CENTERX":   0.0,
            "CENTERY":  0.0,
            "RADIUS":  0.0,
            "SP_VEL":  0,
            "ACC":      0,
            "DEC":      0,
            "DIR":      0
            }
    }
    
    stw_fmc={
        "Running" : False, "Pause": False, "Resume": False, "Stop": False, "LimitN": False, "LimitP": False, 
        "Home": False, "HomeDone": False, "AutoRun": False, "LimitN_None": False, "LimitP_None": False, "Home_None": False, "Home_Overtime": False
    }
    
    ctw_plc={
        "AbsXY": False, "AbsXZ": False, "AbsYZ": False, "AbsXYZ": False, "ArcXY": False, "ArcXZ": False, "ArcYZ": False, "StopRun": False,
        "JogFwd": False, "JogRev": False, "Abs": False, "Rel": False, "Home": False, "Stop": False, "Pause": False, "Reset": False  
    }
    
    stw_cam = {
        "ERROR": False, "READY": False, "BUSY": False, "AbsXYZ": False, "free05": False, "free04": False, "OK_W": False, "free06": False,
        "OK_TAIL": False, "ERROR_TAIL": False, "OK_WELD": False, "ERROR_WELD": False, "Home": False, "free01": False, "free10": False, "free11": False  
    }

    ctw_cam = {
        "AEA": False, "AbsXZ": False, "AbsYZ": False, "TRIG_ESME": False, "ArcXY": False, "ArcXZ": False, "TRIG_WELD": False, "TRIG_TAIL": False,
        "TRIG_Nah": False, "JogRev": False, "Abs": False, "TRIG_GA": False, "TRIG_NO": False, "Stop": False, "Pause": False, "Reset": False  
    }

    cam_struc = {
        "TAIL_MEASURE": 0,
        "WELD_MEASURE": 0,
        "ERROR": 0
    }


    mask_fmc = []
    for i in range(4): 
        mask_fmc.append(ctw_mask.copy())
    
    def __init__(self, id, plc_ip, db_status, len_stat, start_fmc_stat, db_control, len_ctrl, start_fmc_ctrl, CtrlFMC):
        self.id = id
        self.plc_ip = plc_ip
        self.db_status = db_status
        self.start_fmc_stat = start_fmc_stat
        self.len_stat = len_stat
        self.db_control = db_control
        self.start_fmc_ctrl = start_fmc_ctrl
        self.len_ctrl = len_ctrl
        self.CtrlFMC = CtrlFMC
        self.plc = snap7.client.Client()
        self.connect_plc()
        super().__init__('http://192.168.90.78:5000/datos_json/', 'http://192.168.90.78:5000/datos_json/status')
        self.listening_datapool = threading.Thread(target=self.proc_data)
        self.listening_datapool.daemon = True
        self.listening_fmc = threading.Thread(target=self.proc_fmc)
        self.listening_fmc.daemon = True
        self.listening_datapool.start()
        
    def __del__(self):
        self.disconnect_plc()    

    def connect_plc(self):
        self.conn = self.plc.connect(self.plc_ip, self.rack, self.slot)
        time.sleep(0.5)
        # Data FMC_STATUS
        self.data_status = self.plc.db_read(self.db_status, 0, self.len_stat)

    def disconnect_plc(self):
        
        self.plc.disconnect()

    def get_plc_data(self):
        
        # Data FMC_CONTROL
        self.data_control = self.plc.db_read(self.db_control, 0, self.len_ctrl)
       
    def set_plc_data(self):
        # Data FMC STATUS
        self.plc.db_write(self.db_status, 0, self.data_status)
        
    def get_fmc_values(self, offset):
        # Parse Values PLC -> FMC
        
        # Axis X - Data Values
        ind = offset + 0
        for par in self.data_struc["AxisX"]:
            if (par != "STW") and (par != "PV_POS") and (par != "PV_VEL"): 
                self.data_struc["AxisX"][par] = util.get_int(self.data_control, ind)
                ind+=2 
        
        # Axis Y - Data Values
        ind = offset + 18
        for par in self.data_struc["AxisY"]:
            if (par != "STW") and (par != "PV_POS") and (par != "PV_VEL"): 
                self.data_struc["AxisY"][par] = util.get_int(self.data_control, ind)
                ind+=2
        
        # Axis Z - Data Values
        ind = offset + 36
        for par in self.data_struc["AxisZ"]:
            if (par != "STW") and (par != "PV_POS") and (par != "PV_VEL"): 
                self.data_struc["AxisZ"][par] = util.get_int(self.data_control, ind)
                ind+=2
        
        # 2Axis XY - Data Values
        ind = offset + 54
        for parXY in self.data_struc["2Axis_XY"]:
            self.data_struc["2Axis_XY"][parXY] = util.get_int(self.data_control, ind)
            ind+=2
        
        # 3Axis XYZ - Data Values    
        ind = offset + 68
        for parXYZ in self.data_struc["3Axis_XYZ"]:
            self.data_struc["3Axis_XYZ"][parXYZ] = util.get_int(self.data_control, ind)
            ind+=2
        
        # ARC XY - Data Values    
        ind = offset + 82
        for parARC in self.data_struc["ARC_XY"]:
            
            if parARC == "SP_POSX" or parARC == "SP_POSY" or parARC == "CENTERX" or parARC == "CENTERY" or parARC == "RADIUS": 
                self.data_struc["ARC_XY"][parARC] = util.get_real(self.data_control, ind)
                ind+=4
            else: 
                self.data_struc["ARC_XY"][parARC] = util.get_int(self.data_control, ind)
                ind+=2

        # Cam - Data Values word
        ind = 448
        # Read word
        word_cam = util.get_int(self.data_control, ind)
        # print("Word Cam: ----------------------------------------> ", word_cam)
        # connvert word_cam into '00000000' string 
        word_cam = bin(word_cam)[2:].zfill(16)
        for parCAM, i in zip(self.ctw_cam, range(16)):
            self.ctw_cam[parCAM] = True if word_cam[i] == '1' else False
   
    def set_fmc_values(self, offset):
        # Parse values FMC -> PLC
        util.set_bool(self.data_status, offset, 0, self.data_struc["SYSTEM"]["LINK"])
        util.set_int(self.data_status, offset+2, self.data_struc["SYSTEM"]["STATUS"])
        util.set_int(self.data_status, offset+4, self.data_struc["SYSTEM"]["INPUTS"])
        util.set_int(self.data_status, offset+6, self.data_struc["SYSTEM"]["OUTPUTS"])
        util.set_word(self.data_status, offset+8, self.data_struc["AxisX"]["STW"])
        util.set_int(self.data_status, offset+10, self.data_struc["AxisX"]["PV_POS"])
        util.set_int(self.data_status, offset+12, self.data_struc["AxisX"]["PV_VEL"])
        util.set_word(self.data_status, offset+14, self.data_struc["AxisY"]["STW"])
        util.set_int(self.data_status, offset+16, self.data_struc["AxisY"]["PV_POS"])
        util.set_int(self.data_status, offset+18, self.data_struc["AxisY"]["PV_VEL"])
        util.set_word(self.data_status, offset+20, self.data_struc["AxisZ"]["STW"])
        util.set_int(self.data_status, offset+22, self.data_struc["AxisZ"]["PV_POS"])
        util.set_int(self.data_status, offset+24, self.data_struc["AxisZ"]["PV_VEL"]) 
        # convert self.stw_cam to word
        num = sum((val << i) for i, val in enumerate(self.stw_cam.values()))
        # word_cam = '0x' + format(num, '04x')
        util.set_word(self.data_status, 104, num)  
        # Write Data cam_struc
        util.set_real(self.data_status, 106, self.cam_struc["TAIL_MEASURE"])
        util.set_real(self.data_status, 110, self.cam_struc["WELD_MEASURE"])
        util.set_int(self.data_status, 114, self.cam_struc["ERROR"])

    
    def comm_axis(self, Axis):
        # print("Axis: {} CTW1:{} Mask:{} Id:{}".format(Axis, self.data_struc[Axis]["CTW"], self.mask_fmc[self.id][Axis], self.id))
        ctw_tmp = self.data_struc[Axis]["CTW"]
        self.data_struc[Axis]["CTW"] = self.data_struc[Axis]["CTW"] & self.mask_fmc[self.id][Axis]
        self.mask_fmc[self.id][Axis] = ctw_tmp ^ 0xFFFF
        # print("CTW2: {} Mask: {} Id: {}".format(self.data_struc[Axis]["CTW"], self.mask_fmc[self.id][Axis], self.id))
        ind = 0x0001
        for x in self.ctw_plc:
            self.ctw_plc[x] = True if self.data_struc[Axis]["CTW"] & ind else False
            ind = ind <<1
        # print(self.ctw_plc)
    
    def axis_move(self, Axis, CtrlFMC):
        AxisId = 0 if Axis == "AxisX" else 1 if Axis == "AxisY" else 2 if Axis == "AxisZ" else 0
        
        self.comm_axis(Axis)
        
        # Jog Move
        if (self.ctw_plc["JogFwd"] ^ self.ctw_plc["JogRev"]) :
            # self.data_post = {"Id": self.id, "AxeId": AxisId, "Pos": 20 if self.ctw_plc["JogFwd"] else -20, "Speed": self.data_struc[Axis]["SP_VEL"], "Acc": self.data_struc[Axis]["ACC"], "Dec": self.data_struc[Axis]["DEC"], "Mode": 1}
            # self.send_data("jog_move")
            pos = 20 if self.ctw_plc["JogFwd"] else -20
            # print("Jog:", self.ctw_plc["JogFwd"], self.ctw_plc["JogRev"], self.id, pos, self.data_struc[Axis]["SP_VEL"], self.data_struc[Axis]["ACC"], self.data_struc[Axis]["DEC"])
            CtrlFMC.jog_Move(AxisId, pos, self.data_struc[Axis]["SP_VEL"], self.data_struc[Axis]["ACC"], self.data_struc[Axis]["DEC"])
             
        # Absolute Move
        if self.ctw_plc["Abs"] :
            # self.data_post = {"Id": self.id, "AxeId": AxisId, "Pos": self.data_struc[Axis]["SP_POS"], "Speed": self.data_struc[Axis]["SP_VEL"], "Acc": self.data_struc[Axis]["ACC"], "Dec": self.data_struc[Axis]["DEC"]}
            # self.send_data("abs_move")
            CtrlFMC.abs_Move(AxisId, self.data_struc[Axis]["SP_POS"], self.data_struc[Axis]["SP_VEL"], self.data_struc[Axis]["ACC"], self.data_struc[Axis]["DEC"])
               
        # Relative Move
        if self.ctw_plc["Rel"] :
            # self.data_post = {"Id": self.id, "AxeId": AxisId, "Pos": self.data_struc[Axis]["SP_POS"], "Speed": self.data_struc[Axis]["SP_VEL"], "Acc": self.data_struc[Axis]["ACC"], "Dec": self.data_struc[Axis]["DEC"]}
            # self.send_data("rel_move")
            CtrlFMC.rel_Move(AxisId, self.data_struc[Axis]["SP_POS"], self.data_struc[Axis]["SP_VEL"], self.data_struc[Axis]["ACC"], self.data_struc[Axis]["DEC"]) 
            
        # Home Move
        if self.ctw_plc["Home"] :
            # self.data_post = {"Id": self.id, "AxeId": AxisId, "Speed": self.data_struc[Axis]["SP_HVEL"], "Acc": self.data_struc[Axis]["HACC"], "Fall": self.data_struc[Axis]["FALL"], "Dir": self.data_struc[Axis]["DIR"]}
            # self.send_data("home_move") 
            CtrlFMC.home_Move(AxisId, self.data_struc[Axis]["SP_HVEL"], self.data_struc[Axis]["HACC"], self.data_struc[Axis]["FALL"], self.data_struc[Axis]["DIR"])
                
        # Stop Move
        if self.ctw_plc["Stop"] :
            # self.data_post = {"Id": self.id, "AxeId": AxisId, "Mode": 1}
            # self.send_data("stop_move")
            CtrlFMC.stop_Axis(AxisId, 1)

    
    def send_http(self, CtrlFMC):
        # Axis X
        self.axis_move("AxisX", CtrlFMC)
        
        # Axis Y
        self.axis_move("AxisY", CtrlFMC)
        
        # Axis Z
        self.axis_move("AxisZ", CtrlFMC)
         
        # 2Axis Move
        self.comm_axis("2Axis_XY")
        if (self.ctw_plc["AbsXY"] ^ self.ctw_plc["AbsXZ"] ^ self.ctw_plc["AbsYZ"]) :
            axe = 3 if self.ctw_plc["AbsXY"] else 5 if self.ctw_plc["AbsXZ"] else 6 if self.ctw_plc["AbsYZ"] else 3
                
            CtrlFMC.move_2Axis(axe, self.data_struc["2AxisS_XY"]["SP_POSX"], self.data_struc["2Axis_XY"]["SP_POSY"], self.data_struc["2Axis_XY"]["SP_VEL"], self.data_struc["2Axis_XY"]["ACC"], self.data_struc["2Axis_XY"]["DEC"])
        if self.ctw_plc["StopRun"]:
            CtrlFMC.stop_Run(self.id)
            
        # 3Axis Move
        self.comm_axis("3Axis_XYZ")
        if self.ctw_plc["AbsXYZ"] :
            
            CtrlFMC.move_3Axis(self.data_struc["3Axis_XYZ"]["SP_POSX"], self.data_struc["3Axis_XYZ"]["SP_POSY"], self.data_struc["3Axis_XYZ"]["SP_POSZ"], self.data_struc["3Axis_XYZ"]["SP_VEL"], self.data_struc["3Axis_XYZ"]["ACC"], self.data_struc["3Axis_XYZ"]["DEC"])
        if self.ctw_plc["StopRun"]:
            CtrlFMC.stop_Run(self.id)
                    
        # 2Arc Move
        self.comm_axis("ARC_XY")
        if (self.ctw_plc["ArcXY"] ^ self.ctw_plc["ArcXZ"] ^ self.ctw_plc["ArcYZ"]) :
            axe = 3 if self.ctw_plc["ArcXY"] else 5 if self.ctw_plc["ArcXZ"] else 6 if self.ctw_plc["ArcYZ"] else 3
            # print("Move Arc: ", self.id, self.data_struc["ARC_XY"])
            CtrlFMC.move_Arc2Axis(axe, self.data_struc["ARC_XY"]["SP_POSX"], self.data_struc["ARC_XY"]["SP_POSY"], self.data_struc["ARC_XY"]["CENTERX"], self.data_struc["ARC_XY"]["CENTERY"], self.data_struc["ARC_XY"]["RADIUS"], self.data_struc["ARC_XY"]["SP_VEL"], self.data_struc["ARC_XY"]["ACC"], self.data_struc["ARC_XY"]["DEC"], self.data_struc["ARC_XY"]["DIR"])
        if self.ctw_plc["StopRun"]:
            # print("Stop Run Command")
            CtrlFMC.stop_Run(self.id) 
               
    def stw_proc(self, status: int):
        ind = 1
        for x in self.stw_fmc:
            self.stw_fmc[x] = True if status & ind else False
            ind = ind<<1
        # print("Status1: ", self.stw_fmc)
        stw = 0
        stw = (stw | 0x0100) if self.stw_fmc["Running"] else (stw & 0xfeff) #Run
        stw = (stw | 0x0200) if self.stw_fmc["Stop"] else (stw & 0xfdff) #Stop
        stw = (stw | 0x0400) if self.stw_fmc["Home"] else (stw & 0xfbff) #Home
        stw = (stw | 0x0800) if self.stw_fmc["LimitN"] else (stw & 0xf7ff) #LimN
        stw = (stw | 0x1000) if self.stw_fmc["LimitP"] else (stw & 0xefff) #LimP
        stw = (stw | 0x4000) if self.stw_fmc["LimitN"] or self.stw_fmc["LimitP"] else (stw & 0xbfff) #Lock
        stw = (stw | 0x8000) if self.stw_fmc["Home"] else (stw & 0x7fff) #Home Done
        # print("Status2: ", stw)
        return stw
 
    def recieve_http(self, CtrlFMC):
        # get_data = self.receive_data(self.id)  
        # Data I/O 
        self.data_struc['SYSTEM']['INPUTS'] = int(CtrlFMC.ms.inputStatus[0]) # int(get_data['Inputs']) 
        self.data_struc['SYSTEM']['OUTPUTS'] = int(CtrlFMC.ms.outputStatus[0]) # int(get_data['Outputs'])
        # Data Axis X
        self.data_struc['AxisX']['PV_POS'] = round(float(CtrlFMC.ms.realPos[0])) # round(float(get_data['PosX']))
        self.data_struc['AxisX']['STW'] = self.stw_proc(int(CtrlFMC.ms.axisStatus[0])) #get_data['StatX']
        # Data Axis Y
        self.data_struc['AxisY']['PV_POS'] = round(float(CtrlFMC.ms.realPos[1])) #round(float(get_data['PosY']))
        self.data_struc['AxisY']['STW'] = self.stw_proc(int(CtrlFMC.ms.axisStatus[1])) # get_data['StatY']
        # Data Axis Y
        self.data_struc['AxisZ']['PV_POS'] = round(float(CtrlFMC.ms.realPos[2])) #round(float(get_data['PosZ']))
        self.data_struc['AxisZ']['STW'] = self.stw_proc(int(CtrlFMC.ms.axisStatus[2])) # get_data['StatZ']
        
        # print("FMC AxisX: ",self.data_struc['AxisX']['PV_POS'])
        # print("FMC AxisY: ",self.data_struc['AxisY']['PV_POS'])
        # print("FMC AxisZ: ",self.data_struc['AxisZ']['PV_POS'])
    
    def FMC_S7(self, CtrlFMC, offset_stat, offset_ctrl):
        
        self.get_fmc_values(offset_ctrl)
        self.send_http(CtrlFMC)
        self.recieve_http(CtrlFMC)
        self.set_fmc_values(offset_stat)
    
    def proc_data(self):
        
        while(True):
            
            axis_addr =[[0, 0], [26, 112], [52, 224], [78, 336]]
            
            start_time_total = time.perf_counter()

            try:    
                # Verify plc connection
                if self.plc.get_connected() == False:
                    self.connect_plc()
                    # print
                    print("Reconnecting PLC: ", self.id, self.plc_ip)
                    continue
                self.get_plc_data()
        
                for x in range(4):
                    start_time = time.perf_counter()
                    self.id = x

                    # Verify conection and status
                    
                    st = self.CtrlFMC[self.id].get_Status()
                    if st == -1:
                        req_stat = [None]  # Mutable var so the function can store the result
                        def func():
                            req_stat[0] = self.CtrlFMC[self.id].disconnect_Machine()
                            req_stat[0] = self.CtrlFMC[self.id].connect_Machine()

                        thread = threading.Thread(target=func)
                        thread.start()

                        # Wait for 2 seconds or until the thread finishes, whichever comes first
                        thread.join(timeout=2)

                        if thread.is_alive():
                            print("-> Timeout Check from ClientS7 - Connection: ", self.id)
                        
                        continue 
                                        
                    if x == 0:
                        if self.CtrlFMC[self.id].Axis_RealPos[0] >= 1500:
                            self.CtrlFMC[self.id].set_Output(0,1)
                        else: self.CtrlFMC[self.id].set_Output(0,0)
                        
                        if self.CtrlFMC[self.id].Axis_RealPos[0] >= 2200:
                            self.CtrlFMC[self.id].set_Output(1,1)
                        else: self.CtrlFMC[self.id].set_Output(1,0)
                        
                        if self.CtrlFMC[self.id].Axis_RealPos[1] >= 2215 or self.CtrlFMC[self.id].Axis_RealPos[1] <= 1510:
                                self.CtrlFMC[self.id].set_Output(2,1)
                        else: self.CtrlFMC[self.id].set_Output(2,0)
                        
                        if self.CtrlFMC[self.id].Axis_RealPos[2] >= 1950:
                                self.CtrlFMC[self.id].set_Output(3,1)
                        else: self.CtrlFMC[self.id].set_Output(3,0)
                    
                        
                    self.FMC_S7(self.CtrlFMC[self.id], axis_addr[x][0], axis_addr[x][1])
                    # self.CtrlFMC[self.id].disconnect_Machine()
        
                    end_time = time.perf_counter()
                    # print(end_time - start_time, self.id, "seconds FMC")
                self.set_plc_data()
                end_time_total = time.perf_counter()
                # print(end_time_total - start_time_total, self.id, "seconds FMC") 
            except RuntimeError as e:
                print("Runtime Error: ", e)
                self.disconnect_plc()
                continue
       
    
    def proc_fmc(self):
        
        pass
        
        
            
            



