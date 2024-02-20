from enum import Enum


class HardwareConnectionType(str, Enum):
    OSC = "OSC"
    SLIPSERIAL = "SlipSerial"
