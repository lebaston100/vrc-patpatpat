"""
This module houses all possibel OSC connection messages as dataclasses
"""

from dataclasses import dataclass, field
from datetime import datetime

from utils.Enums import HardwareConnectionType


@dataclass(frozen=True)
class HeartbeatMessage:
    """An incoming Heartbeat message.

    Attributes:
        mac (str): The (wifi) mac of the sending hardware device
        uptime (int): The uptime of the hardware device in seconds
        vccBat (int): The current battery voltage
        rssi (int): The wifi rssi
        sourceAddr (list[str, int]): The ip/port of the osc socket
        ts (int): The time the object was created (aka received)
    """

    mac: str = "00:00:00:00:00:00"
    uptime: int = 0
    vccBat: float = 0
    rssi: int = 0
    sourceAddr: str = ""
    ts: datetime = field(default_factory=datetime.now)

    @staticmethod
    def isType(topic: str, params: tuple) -> bool:
        return topic == "/patpatpat/heartbeat" and len(params) == 4


@dataclass(frozen=True)
class DiscoveryResponseMessage:
    """An incoming response to a device discovery request.

    Attributes:
        mac (str): The (wifi) mac of the sending hardware device
        hostname (str): The hardware devices hostname
        numMotors (int): The max amount of output channels
            as configured in the hardware device
        sourceType (str): The origin of the message, "OSC" or "SlipSerial"
        sourceAddr (str): The osc device ip or serial port name
        ts (int): The time the object was created (aka received)
    """

    mac: str = "00:00:00:00:00:00"
    hostname: str = ""
    numMotors: int = 0
    sourceType: str | HardwareConnectionType = ""
    sourceAddr: str = ""
    ts: datetime = field(default_factory=datetime.now)

    @staticmethod
    def isType(topic: str, params: tuple) -> bool:
        return topic == "/patpatpat/noticeme/senpai" and len(params) == 3


if __name__ == "__main__":
    print("There is no point running this file directly")
