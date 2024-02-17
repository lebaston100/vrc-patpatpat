"""This module handles all the communication with the hardware devices
including discovery
"""

import socket
from typing import TYPE_CHECKING, TypeVar

from PyQt6.QtCore import QObject, QThread, QTimer
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_message_builder import ArgValue
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from modules import config
from modules.GlobalConfig import GlobalConfigSingleton
from modules.OscMessageTypes import DiscoveryResponseMessage, HeartbeatMessage
from utils import LoggerClass, threadAsStr

logger = LoggerClass.getSubLogger(__name__)


class HwManager(QObject):
    """Handles all hardware related tasks
    """

    hwListUpdated = QSignal(dict)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        # Start osc device discovery
        self.hwOscDiscoveryTx = HwOscDiscoveryTx()
        self.hwOscDiscoveryTx.start()

        # Start osc receiver
        self.hwOscRx = HwOscRx()

        self.hardwareDevices: dict[int, object]

    def writeSpeed(self, espId: int = 0, channelId: int = 0, value: float | int = 0) -> None:
        """Write speed from motor into esp's state buffer

        Args:
            espId (int, optional): The destined esp. Defaults to 0.
            channelId (int, optional): The destined esp's channel. Defaults to 0.
            value (float | int, optional): The value to write. Defaults to 0.
        """
        ...

    def sendHwUpdate(self, espId: int = 0) -> None:
        """Triggers a sendPinValues() on the destined Hardware

        Args:
            espId (int, optional): Id of the destined HardwareDevice. Defaults to 0.
        """
        ...

    def _checkDeviceExistance(self, mac: str) -> int | None:
        """Checks config if given mac adress already exists

        Args:
            mac (str): The mac adress to look for

        Returns:
            int | None: If mac is found in config, it's id, otherwise None
        """

        hardwareDevices = config.get("esps")
        return next((device["id"] for device in hardwareDevices.values()
                     if device["wifiMac"] == mac), None)

    def close(self) -> None:
        """Closes everything hardware related
        """

        logger.debug(f"Stopping {__class__.__name__}")
        if hasattr(self, "hwOscDiscoveryTx"):
            self.hwOscDiscoveryTx.stop()
        if hasattr(self, "hwOscRx"):
            self.hwOscRx.close()


class HwOscDiscoveryTx(QObject):
    """Sends out hardware discovery broadcasts on all interfaces
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initializes the HwOscDiscoveryTx object.
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._interfaces = socket.getaddrinfo(
            host=socket.gethostname(), port=None, family=socket.AF_INET)
        self._sockets: list[SimpleUDPClient] = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.timerEvent)

    def start(self, interval: int = 3) -> None:
        """Starts the timer with the specified interval.

        Args:
            interval: The interval in seconds. Default is 3.
        """

        if interval:
            self._interval = interval
        if self._timer.isActive():
            self.stop()

        for interface in self._interfaces:
            client = SimpleUDPClient(
                "255.255.255.255", 8888, allow_broadcast=True, family=socket.AF_INET)
            client._sock.bind((interface[-1][0], 8871))
            self._sockets.append(client)
        self._timer.start(self._interval * 1000)

    def stop(self) -> None:
        """Stops the timer and closes all sockets.
        """

        logger.debug(f"Stopping {__class__.__name__}")
        for client in self._sockets:
            client._sock.shutdown(socket.SHUT_RDWR)
            client._sock.close()
        self._sockets = []
        self._timer.stop()

    def timerEvent(self) -> None:
        """Send out discovery messages when timer fires
        """

        # logger.debug("Sending out discovery broadcasts")
        for client in self._sockets:
            client.send_message("/patpatpat/discover", [])
        # logger.debug("Done sending out discovery broadcasts")


class HwOscRxWorker(QObject):
    """The thread receiving osc messages from hardware devices
    """

    gotDiscoveryReply = QSignal(object)
    gotOscHardwareHeartbeat = QSignal(object)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.dispatcher = Dispatcher()
        self.dispatcher.map("/patpatpat/noticeme/senpai",
                            self._handleDiscoveryResponseMessage,
                            needs_reply_address=True)
        self.dispatcher.map("/patpatpat/heartbeat",
                            self._handleHeartbeatMessage,
                            needs_reply_address=True)
        self.dispatcher.set_default_handler(self._defaultHandler)

    def _defaultHandler(self, topic: str, *args) -> None:
        logger.debug(f"Unknown osc message: {topic}, {str(args)}")

    def _handleDiscoveryResponseMessage(self, client: tuple,
                                        topic: str, *args) -> None:
        # logger.debug(f"_handleDiscoveryResponseMessage: {str(client)}, {topic}, {str(args)}")
        if DiscoveryResponseMessage.isType(topic, args):
            msg = DiscoveryResponseMessage(*args, source=client[0])
            logger.debug(msg)
            self.gotDiscoveryReply.emit(msg)

    def _handleHeartbeatMessage(self, client: tuple,
                                topic: str, *args) -> None:
        # logger.debug(f"_handleHeartbeatMessage: {str(client)}, {topic}, {str(args)}")
        if HeartbeatMessage.isType(topic, args):
            msg = HeartbeatMessage(*args, source=client[0])
            logger.debug(msg)
            self.gotOscHardwareHeartbeat.emit(msg)

    @QSlot()
    def startOscServer(self) -> None:
        logger.info(
            f"startOsc pid     ={threadAsStr(QThread.currentThread())}")
        logger.info(
            f"startOsc pid_self={threadAsStr(self.thread())}")
        logger.info(f"starting osc server on port 8872")
        try:
            self._oscRx = BlockingOSCUDPServer(("", 8872), self.dispatcher)
            self._oscRx.serve_forever()
        except Exception as E:
            logger.exception(E)
        logger.info("startOsc done, cleaning up...")
        self._oscRx.socket.close()
        del self._oscRx  # dereferene so the gc can pick it up

    def closeOscServer(self) -> None:
        """Stops and closes the osc server
        """

        logger.debug(f"closeOscServer in {__class__.__name__}")
        selfThread = self.thread()
        logger.debug(f"pid_QThread.currentThread={threadAsStr(QThread.currentThread())} "
                     f"pid_selfThread={threadAsStr(selfThread)} ")
        if hasattr(self, "_oscRx"):
            self._oscRx.shutdown()
        if selfThread:
            selfThread.quit()
            selfThread.wait()


class HwOscRx(QObject):
    """The Thread Manager for the global Hardware Osc Receiver
    """

    gotDiscoveryReply = QSignal(object)
    gotOscHardwareHeartbeat = QSignal(object)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.worker = HwOscRxWorker()
        self.workerThread = QThread()
        self.workerThread.started.connect(self.worker.startOscServer)
        self.worker.moveToThread(self.workerThread)

        # relay signals
        self.worker.gotDiscoveryReply.connect(self.gotDiscoveryReply)
        self.worker.gotOscHardwareHeartbeat.connect(
            self.gotOscHardwareHeartbeat)

        logger.debug("Starting heartbeat osc server and client")
        self.workerThread.start()

    def close(self) -> None:
        """Closes everything heartbeat osc related
        """
        logger.debug("Closing heartbeat osc")
        self.worker.closeOscServer()
        self.workerThread.quit()
        self.workerThread.wait()


if __name__ == "__main__":
    print("There is no point running this file directly")
