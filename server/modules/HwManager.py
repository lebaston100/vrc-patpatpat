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
from pythonosc.dispatcher import Dispatcher
from modules.GlobalConfig import GlobalConfigSingleton
from utils import LoggerClass, threadAsStr
from modules.OscMessageTypes import HeartbeatMessage, DiscoveryResponseMessage

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
