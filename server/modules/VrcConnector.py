from datetime import datetime
from time import time

from PyQt6.QtCore import QObject, QThread, QTimer
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from pythonosc import osc_packet
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_message_builder import ArgValue
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from modules.GlobalConfig import GlobalConfigSingleton
from utils.Logger import LoggerClass
from utils.threadToStr import threadAsStr

logger = LoggerClass.getSubLogger(__name__)
config = GlobalConfigSingleton.getInstance()


class IVrcConnector():
    """The interface for server <-> vrc communication."""

    onVrcContact = QSignal(float, str, list)
    onVrcConnectionStateChanged = QSignal(bool)

    def connect(self):
        """A generic connect method to be reimplemented."""
        raise NotImplementedError

    def close(self):
        """A generic close method to be reimplemented."""
        raise NotImplementedError

    def restart(self):
        """A generic restart method to be reimplemented."""
        raise NotImplementedError

    def send(self):
        """A generic send method to be reimplemented."""
        raise NotImplementedError

    def addToFilter(self, relativePath: str):
        """A generic addToFilter method to be reimplemented."""
        raise NotImplementedError

    def removeFromFilter(self, relativePath: str):
        """A generic removeFromFilter method to be reimplemented."""
        raise NotImplementedError


class VrcConnectionWorker(QObject):
    def __init__(self, connector, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)
        self._connector = connector
        self.dispatcher = VrcOscDispatcher(self._connector)

    def loadSettings(self) -> None:
        self._oscRxPort = config.get("program.vrcOscSendPort", 9000)
        self._oscTxIp = config.get("program.vrcOscReceiveAddress", "127.0.0.1")
        self._oscTxPort = config.get("program.vrcOscReceivePort", 9001)

    @QSlot()
    def startOscServer(self) -> None:
        logger.debug(
            f"startOsc pid     ={threadAsStr(QThread.currentThread())}")
        logger.debug(
            f"startOsc pid_self={threadAsStr(self.thread())}")
        logger.debug(f"Starting osc server on port {str(self._oscRxPort)}")
        try:
            self._oscRx = BlockingOSCUDPServer(
                ("", self._oscRxPort), self.dispatcher)
            self._oscRx.serve_forever()
        except Exception as E:
            logger.exception(E)
        logger.debug("startOsc done, cleaning up...")
        self._oscRx.socket.close()
        del self._oscRx  # dereferene so the gc can pick it up

    @QSlot()
    def closeOscServer(self) -> None:
        """Restarts the thread that is running us
        self.thread returns the thread, but the thread is not the actual
        thread but instead the thread's manager running in the main thread"""
        logger.debug(f"closeOscServer in {__class__.__name__}")
        selfThread = self.thread()
        logger.debug(f"pid_QThread.currentThread={threadAsStr(QThread.currentThread())} "
                     f"pid_selfThread={threadAsStr(selfThread)} ")
        if hasattr(self, "_oscRx"):
            self._oscRx.shutdown()
        if selfThread:
            selfThread.quit()
            selfThread.wait()

    def startOscSender(self) -> None:
        self._oscTx = SimpleUDPClient(self._oscTxIp, self._oscTxPort)

    def closeOscSender(self) -> None:
        if hasattr(self, "_oscTx"):
            self._oscTx._sock.close()
            del self._oscTx

    def sendOsc(self, path: str, values: ArgValue) -> None:
        if hasattr(self, "_oscTx"):
            self._oscTx.send_message(path, values)


class VrcConnectorImpl(IVrcConnector, QObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self._lastVrcMessage: datetime | None = None
        self.currentDataState = False
        self.worker = VrcConnectionWorker(self)
        self.worker.loadSettings()
        self.workerThread = QThread()

        self.workerThread.started.connect(self.worker.startOscServer)
        self.worker.moveToThread(self.workerThread)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._timerEvent)
        self._timer.start(1000)

        config.configRootUpdateDone.connect(self._oscGeneralConfigChanged)

    def _receivedOsc(self, client: tuple, addr: str, params: list) -> None:
        """Just a test function that prints if osc event was fired."""
        logger.info(f"osc from {str(client)}: addr={addr} msg={str(params)}")

    @QSlot()
    def _timerEvent(self) -> None:
        """Handle calculation of the connection to vrc based on if data
        is beeing received (with a timeout).
        This is not used for the Contact Groups.
        """
        # TODO: This could be improved to trigger instantly when data comes in
        if not self.currentDataState and self._lastVrcMessage and \
                (datetime.now() - self._lastVrcMessage).total_seconds() <= 3:
            self.currentDataState = True
            logger.debug("VRC connection state changed to "
                         f"{self.currentDataState}")
            self.onVrcConnectionStateChanged.emit(self.currentDataState)
        elif self.currentDataState and self._lastVrcMessage and \
                (datetime.now() - self._lastVrcMessage).total_seconds() > 3:
            self.currentDataState = False
            logger.debug("VRC connection state changed to "
                         f"{self.currentDataState}")
            self.onVrcConnectionStateChanged.emit(self.currentDataState)

    def connect(self) -> None:
        """Start worker thread and osc sender"""
        logger.debug("Starting vrc osc server and client")
        self.workerThread.start()
        self.worker.startOscSender()

    def close(self) -> None:
        """Closes everything vrc osc related."""
        logger.debug("Closing vrc osc server and client")
        self.worker.closeOscSender()
        self.worker.closeOscServer()
        self.workerThread.quit()
        self.workerThread.wait()

    def restart(self) -> None:
        """Close and restart sockets."""
        logger.debug("Restarting vrc osc server and client")
        self.close()
        self.connect()

    def send(self, path: str, values: ArgValue) -> None:
        """Send an osc message to VRChat via the worker.

        Args:
            path (str): The osc path
            values (Any osc supported): The osc values
        """
        self.worker.sendOsc(path, values)

    def addToFilter(self, relativePath: str) -> None:
        if relativePath not in self.worker.dispatcher.matchTopics:
            self.worker.dispatcher.matchTopics.append(relativePath)
            logger.debug(f"Added {relativePath} to vrc osc filter")

    def removeFromFilter(self, relativePath: str) -> None:
        if relativePath in self.worker.dispatcher.matchTopics:
            self.worker.dispatcher.matchTopics.remove(relativePath)
            logger.debug(f"Removed {relativePath} from vrc osc filter")

    def _oscGeneralConfigChanged(self, root: str) -> None:
        if root.startswith("program."):
            self.worker.loadSettings()
            self.restart()


"""
A drop-in replacement of the original osc dispatcher modified
to have less overhead to faster handle the data coming from vrc
"""

class VrcOscDispatcher(Dispatcher):
    """A custom dispatcher for OSC messages.

    This class overwrites some functionalities in the OSC library to
    optimize the processing time of OSC messages. This is safe as the
    overwritten functionalities are not required in this case.

    Attributes:
        _connector (OSCWorker): The OSC connector.
    """

    def __init__(self, connector) -> None:
        """Initializes the VrcOscDispatcher.

        The superclass's __init__ method is intentionally not called.

        Args:
            connector (OSCWorker): The OSC connector.
        """
        self._connector: VrcConnectorImpl = connector
        self.matchTopics = []

    def call_handlers_for_packet(self, data: bytes,
                                 client_address: tuple[str, int]) -> None:
        """Handles incoming OSC packets.

        Parses the incoming OSC packet and emits a signal if the message
        address starts with "/avatar/parameters/". Logs a debug message
        for each incoming OSC message and if the OSC packet could not
        be parsed.

        Args:
            data (bytes): The incoming OSC packet data.
        """
        try:
            packet = osc_packet.OscPacket(data)
            for msg in packet.messages:
                if msg.message.address.startswith("/avatar/parameters/") \
                        and msg.message.address[19:] in self.matchTopics:
                    # pid = threadAsStr(QThread.currentThread())
                    # logger.debug(
                    # f"pid={pid} incoming osc: "
                    # f"addr={msg.message.address} "
                    # f"msg={str(msg.message.params)}"
                    # )
                    self._connector.onVrcContact.emit(
                        time(),
                        msg.message.address,
                        msg.message.params
                    )
            self._connector._lastVrcMessage = datetime.now()
        except osc_packet.ParseError:
            logger.error("Could not parse osc message")


if __name__ == "__main__":
    print("There is no point running this file directly")
