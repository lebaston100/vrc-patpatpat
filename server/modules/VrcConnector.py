import ctypes
from typing import TYPE_CHECKING, TypeVar

from PyQt6.QtCore import QObject, QThread
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from pythonosc.osc_server import BlockingOSCUDPServer

from modules.VrcOscDispatcher import VrcOscDispatcher
from utils import LoggerClass

from modules.GlobalConfig import GlobalConfigSingleton
# T = TypeVar('T', bound='GlobalConfigSingleton')

logger = LoggerClass.getSubLogger(__name__)


def threadAsStr(thread: QThread | None) -> str:
    if thread:
        return str(int(thread.currentThreadId()))  # type:ignore
    return "Unknown"


class VrcConnectionWorker(QObject):
    def __init__(self):
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__()

    def loadSettings(self, config: GlobalConfigSingleton):
        self.port = config.get("program.vrcOscPort", 8000)

    @QSlot()
    def startOsc(self):
        logger.info(
            f"pid     ={threadAsStr(QThread.currentThread())} startOsc")
        logger.info(
            f"pid_self={threadAsStr(self.thread())} startOsc")
        self.dispatcher = VrcOscDispatcher(self)
        logger.info(f"starting osc on port {str(self.port)}")
        self.oscRecv = BlockingOSCUDPServer(
            ("127.0.0.1", self.port), self.dispatcher)
        self.oscRecv.serve_forever()
        logger.info("startOsc done, cleaning up...")
        self.oscRecv.socket.close()
        del self.oscRecv  # dereferene so the gc can pick it up

    def _receivedOsc(self, client: tuple, addr: str, params: list):
        logger.info(f"osc from {str(client)}: addr={addr} msg={str(params)}")

    @QSlot()
    def close(self):
        """stop the infinite osc receiver loop
        """
        logger.debug(f"close in {__class__.__name__}")
        if hasattr(self, "oscRecv"):
            self.oscRecv.shutdown()

    def restart(self):
        """Restarts the thread that is running us
        self.thread returns the thread, but the thread is not the actual
        thread but instead the thread's manager running in the main thread"""
        selfThread = self.thread()
        logger.debug(f"pid_QThread.currentThread={threadAsStr(QThread.currentThread())} "
                     f"pid_selfThread={threadAsStr(selfThread)} ")
        self.close()
        if selfThread:
            selfThread.quit()
            selfThread.wait()
            selfThread.start()


class IVrcConnector():
    """ The interface """
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


class VrcConnectorImpl(IVrcConnector, QObject):
    def __init__(self, config: GlobalConfigSingleton) -> None:
        super().__init__()
        self.config = config
        self.worker = VrcConnectionWorker()
        self.worker.loadSettings(self.config)
        self.workerThread = QThread()

        self.workerThread.started.connect(self.worker.startOsc)
        self.worker.moveToThread(self.workerThread)
        # self.worker.gotVrcContact.connect(self.timerworker.processOsc)
        # self.btn_stopOsc.clicked.connect(self.oscworker.close, Qt.ConnectionType.DirectConnection)
        # self.btn_startOsc.clicked.connect(self.oscworker.start_osc)

        self.config.registerChangeCallback(
            r"program\.vrcOscPort", self._configChanged)

    def connect(self):
        """ Start worker thread """
        self.workerThread.start()

    def close(self):
        """Closes everything vrc osc related
        """
        self.worker.close()
        self.workerThread.quit()
        self.workerThread.wait()

    def restart(self):
        """ Close and restart sockets """
        self.close()
        self.connect()

    def isAlive(self):
        # Not sure about this one yet, maybe signal based instead
        """ TODO """
        raise NotImplementedError

    def send(self):
        """ TODO """
        raise NotImplementedError

    def _configChanged(self, key):
        if key == "program.vrcOscPort":
            self.worker.loadSettings(self.config)
            self.restart()


if __name__ == "__main__":
    print("There is no point running this file directly")
