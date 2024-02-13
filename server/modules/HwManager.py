"""This module handles all the communication with the hardware devices
including discovery
"""

from typing import TYPE_CHECKING, TypeVar

from PyQt6.QtCore import QObject, QThread
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from pythonosc.osc_message_builder import ArgValue
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from modules.GlobalConfig import GlobalConfigSingleton
from modules.VrcOscDispatcher import VrcOscDispatcher
from utils import LoggerClass, threadAsStr

logger = LoggerClass.getSubLogger(__name__)


class HwManager(QObject):
    """
    """
    ...


class HwOscDiscoveryTx(QObject):
    """
    """
    ...


class HwOscRxWorker(QObject):
    """
    """
    ...


class HwOscRx(QObject):
    """
    """
    ...
