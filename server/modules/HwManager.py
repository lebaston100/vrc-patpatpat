"""This module handles all the communication with the hardware devices
including discovery
"""

import socket
from typing import TYPE_CHECKING, TypeVar

from PyQt6.QtCore import QObject, QThread, QTimer, QTimerEvent
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_message_builder import ArgValue
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from modules.GlobalConfig import GlobalConfigSingleton
from modules.OscMessageTypes import DiscoveryResponseMessage, HeartbeatMessage
from utils import LoggerClass, threadAsStr

logger = LoggerClass.getSubLogger(__name__)


class HwManager(QObject):
    """Handles all hardware related tasks
    """

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.hwOscDiscoveryTx = HwOscDiscoveryTx()
        self.hwOscDiscoveryTx.start()

    def close(self):
        """Closes everything hardware related
        """

        logger.debug(f"Stopping {__class__.__name__}")
        if hasattr(self, "hwOscDiscoveryTx"):
            self.hwOscDiscoveryTx.stop()


class HwOscDiscoveryTx(QObject):
    """Sends out hardware discovery broadcasts on all interfaces
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initializes the HwOscDiscoveryTx object.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._interfaces = socket.getaddrinfo(
            host=socket.gethostname(), port=None, family=socket.AF_INET)
        self._sockets: list[SimpleUDPClient] = []
        logger.debug(self._interfaces)

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

    def _defaultHandler(self, topic: str, *args):
        logger.debug(f"Unknown osc message: {topic}, {str(args)}")

    def _handleDiscoveryResponseMessage(self, client: tuple,
                                        topic: str, *args) -> None:
        logger.debug("_handleDiscoveryResponseMessage: "
                     f"{str(client)}, {topic}, {str(args)}")
        if DiscoveryResponseMessage.isType(topic, args):
            msg = DiscoveryResponseMessage(*args, source=[*client])
            logger.debug(msg)
            self.gotDiscoveryReply.emit(msg)

    def _handleHeartbeatMessage(self, client: tuple,
                                topic: str, *args) -> None:
        logger.debug("_handleHeartbeatMessage: "
                     f"{str(client)}, {topic}, {str(args)}")
        if HeartbeatMessage.isType(topic, args):
            msg = HeartbeatMessage(*args, source=[*client])
            logger.debug(msg)
            self.gotOscHardwareHeartbeat.emit(msg)

    @QSlot()
    def startOscServer(self):
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

    def closeOscServer(self):
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

    def close(self):
        """Closes everything heartbeat osc related
        """
        logger.debug("Closing heartbeat osc")
        self.worker.closeOscServer()
        self.workerThread.quit()
        self.workerThread.wait()


if __name__ == "__main__":
    print("There is no point running this file directly")
