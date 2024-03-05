from enum import Enum


class HardwareConnectionType(str, Enum):
    NONE = ""
    OSC = "OSC"
    SLIPSERIAL = "SlipSerial"


class SolverType(str, Enum):
    MLAT = "MLat"
    SINGLEN2N = "Single n:n"
    LINEARGROUP = "Linear Group"
    DPSLINEAR = "DPS Linear"


class VisualizerType(str, Enum):
    MLAT = 0
