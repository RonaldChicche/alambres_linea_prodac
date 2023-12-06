from ctypes import *

#Status I/O controlador
DOut0 = c_int(0)
DOut1 = c_int(1)
DOut2 = c_int(2)
DOut3 = c_int(3)

DIn0 = c_int(0)
DIn1 = c_int(1)
DIn2 = c_int(2)
DIn3 = c_int(3)

axisX = c_int(0)
axisY = c_int(1)
axisZ = c_int(2)
axisXY = c_uint(0x03)
axisXZ = c_uint(0x05)
axisYZ = c_uint(0x06)
arcXY = c_int(0x07)


# Status de controlador FMC4030
class machine_status(Structure):
    _fields_ = [
        ("realPos", c_float * 3),
        ("realSpeed", c_float * 3),
        ("inputStatus", c_int32 * 1),
        ("outputStatus", c_int32 * 1),
        ("limitNStatus", c_int32 * 1),
        ("limitPStatus", c_int32 * 1),
        ("machineRunStatus", c_int32 * 1),
        ("axisStatus", c_int32 * 3),
        ("homeStatus", c_int32 * 1),
        ("file", c_ubyte * 600)
    ]