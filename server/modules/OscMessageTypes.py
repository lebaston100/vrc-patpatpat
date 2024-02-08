"""
This module houses all possibel OSC connection messages as dataclasses
"""

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class HeartbeatMessage:
    """
    An incoming Heartbeat message

    Attributes:
        mac (str): The (wifi) mac of the sending esp
        uptime (int): The uptime of the esp in seconds
        vccBat (int): The current battery voltage
        rssi (int): the wifi rssi
    """

    mac: str = "00:00:00:00:00:00"
    uptime: int = 0
    vccBat: int = 0
    rssi: int = 0

    @staticmethod
    def isType(topic: str, params: list) -> bool:
        return topic == "/patpatpat/heartbeat" and len(params) == 4


@dataclass(frozen=True)
class DiscoveryResponseMessage:
    """
    An incoming response to a device discovery request

    Attributes:
        mac (str): The (wifi) mac of the sending esp
        numMotors (int): The max amount of output channels
            as configured in the esp
    """

    mac: str = "00:00:00:00:00:00"
    numMotors: int = 0

    @staticmethod
    def isType(topic: str, params: list) -> bool:
        return topic == "/patpatpat/noticeme/senpai" and len(params) == 2


if __name__ == "__main__":
    print("There is no point running this file directly")
