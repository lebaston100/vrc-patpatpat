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

# T = TypeVar('T', bound='GlobalConfigSingleton')

logger = LoggerClass.getSubLogger(__name__)


class IVrcConnector():
    """ The interface for server <-> vrc communication"""

    gotVrcContact = QSignal(tuple, str, list)

    def connect(self):
        """ A generic connect method to be reimplemented"""
        raise NotImplementedError

    def close(self):
        """ A generic close method to be reimplemented"""
        raise NotImplementedError

    def restart(self):
        """ A generic restart method to be reimplemented"""
        raise NotImplementedError

    def isAlive(self):
        # Not sure about this one yet, maybe signal based instead
        """ A generic isAlive method to be reimplemented"""
        raise NotImplementedError

    def send(self):
        """ A generic send method to be reimplemented"""
        raise NotImplementedError

    def addToFilter(self, relativePath: str):
        """ A generic addToFilter method to be reimplemented"""
        raise NotImplementedError

    def removeFromFilter(self, relativePath: str):
        """ A generic removeFromFilter method to be reimplemented"""
        raise NotImplementedError


class VrcConnectionWorker(QObject):
    def __init__(self, connector, *args, **kwargs):
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)
        self._connector = connector
        self.dispatcher = VrcOscDispatcher(self._connector)

    def loadSettings(self, config: GlobalConfigSingleton):
        self._oscRxPort = config.get("program.vrcOscSendPort", 9000)
        self._oscTxIp = config.get("program.vrcOscReceiveAddress", "127.0.0.1")
        self._oscTxPort = config.get("program.vrcOscReceivePort", 9001)

    @QSlot()
    def startOscServer(self):
        logger.info(
            f"startOsc pid     ={threadAsStr(QThread.currentThread())}")
        logger.info(
            f"startOsc pid_self={threadAsStr(self.thread())}")
        logger.info(f"starting osc server on port {str(self._oscRxPort)}")
        try:
            self._oscRx = BlockingOSCUDPServer(
                ("", self._oscRxPort), self.dispatcher)
            self._oscRx.serve_forever()
        except Exception as E:
            logger.exception(E)
        logger.info("startOsc done, cleaning up...")
        self._oscRx.socket.close()
        del self._oscRx  # dereferene so the gc can pick it up

    @QSlot()
    def closeOscServer(self):
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
        # self.sendOsc("/chatbox/input", ["test message"])

    def closeOscSender(self) -> None:
        if hasattr(self, "_oscTx"):
            self._oscTx._sock.close()
            del self._oscTx

    def sendOsc(self, path: str, values: ArgValue) -> None:
        if hasattr(self, "_oscTx"):
            self._oscTx.send_message(path, values)


class VrcConnectorImpl(IVrcConnector, QObject):
    def __init__(self, config: GlobalConfigSingleton, *args, **kwargs) -> None:
        super().__init__()
        self.config = config
        self.worker = VrcConnectionWorker(self)
        self.worker.loadSettings(self.config)
        self.workerThread = QThread()

        self.workerThread.started.connect(self.worker.startOscServer)
        self.worker.moveToThread(self.workerThread)
        # self.gotVrcContact.connect(self._receivedOsc)

        self.config.configRootUpdateDone.connect(self._oscGeneralConfigChanged)

    def _receivedOsc(self, client: tuple, addr: str, params: list):
        """Just a test function that prints if osc event was fired
        """
        logger.info(f"osc from {str(client)}: addr={addr} msg={str(params)}")

    def connect(self):
        """ Start worker thread and osc sender"""
        logger.debug("Starting vrc osc server and client")
        self.workerThread.start()
        self.worker.startOscSender()

    def close(self):
        """Closes everything vrc osc related
        """
        logger.debug("Closing vrc osc server and client")
        self.worker.closeOscSender()
        self.worker.closeOscServer()
        self.workerThread.quit()
        self.workerThread.wait()

    def restart(self):
        """ Close and restart sockets """
        logger.debug("Restarting vrc osc server and client")
        self.close()
        self.connect()

    def isAlive(self):
        # Not sure about this one yet, maybe signal based instead
        """ TODO """
        raise NotImplementedError

    def send(self, path: str, values: ArgValue) -> None:
        """Send an osc message to VRchat via the worker.

        Args:
            path (str): The osc path
            values (Any osc supported): The osc values
        """
        self.worker.sendOsc(path, values)

    def addToFilter(self, relativePath: str):
        if relativePath not in self.worker.dispatcher.matchTopics:
            self.worker.dispatcher.matchTopics.append(relativePath)

    def removeFromFilter(self, relativePath: str):
        if relativePath in self.worker.dispatcher.matchTopics:
            self.worker.dispatcher.matchTopics.remove(relativePath)

    def _oscGeneralConfigChanged(self, root):
        self.worker.loadSettings(self.config)
        self.restart()


if __name__ == "__main__":
    print("There is no point running this file directly")
