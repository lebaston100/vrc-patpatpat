from enum import Enum


class HardwareConnectionType(str, Enum):
    NONE = ""
    OSC = "OSC"
    SLIPSERIAL = "SlipSerial"


class SolverType(str, Enum):
    MLAT = "MLat"
    LINEAR = "Linear"
