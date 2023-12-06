from ctypes import *
from ControllerClass import *



class Sequence():
    #Variables de Proceso
    rows, cols = [5,3]
    cant_total_alambres = 0
    long_total_alambres = 0
    MaxAlambres = rows
    offsetHead = 250
    offsetTail = 150
    Alambre = [[1]*cols]*rows
    
    def __init__(self):
        pass
    
    def __del__(self):
        pass