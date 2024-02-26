from typing import TypeVar

from PyQt6.QtCore import QObject, QThread

from modules import config
from modules.HwManager import HwManager
from modules.Solver import SolverRunner
from modules.VrcConnector import VrcConnectorImpl
from utils import LoggerClass, threadAsStr

logger = LoggerClass.getSubLogger(__name__)

T = TypeVar('T', bound='ServerSingleton')


class ServerSingleton(QObject):
    __instance = None

    @classmethod
    def getInstance(cls: type[T]) -> T:
        """Get the singleton instance.

        Returns:
            ServerSingleton: Singleton instance.
        """

        return cls.__instance

    def __init__(self, *args, **kwargs) -> None:

        if ServerSingleton.__instance:
            raise RuntimeError("Can't initialize multiple singleton instances")

        super().__init__()
        logger.debug(f"Creating {__class__.__name__} in thread "
                     f"{threadAsStr(QThread.currentThread())}")

        self.vrcOscConnector = VrcConnectorImpl(config)
        self.vrcOscConnector.connect()
        # TODO: Connect this to ContactGroups instead
        self.vrcOscConnector.onVrcContact.connect(self._vrcOscDataReceived)
        # self.vrcOscConnector.addToFilter("pat_2")

        self.hwManager = HwManager()

        self._solverRunnerThread = QThread()
        self.solverRunner = SolverRunner(config)

        # self._solverRunnerThread.started.connect(self.solverRunner.runSolvers)
        # self.solverRunner.moveToThread(self._solverRunnerThread)
        # self._solverRunnerThread.start()

        self.hwManager.createAllHardwareDevicesFromConfig()

        ServerSingleton.__instance = self

    def _vrcOscDataReceived(self, ts: float, addr: str, params: list) -> None:
        """Handle osc data coming from VRChat.
        We can distribute the contacts to the right signal here.

        Args:
            client (tuple): Remote ip/port
            addr (str): The osc path
            params (list): The parameter list depnding on the addr
        """
        logger.info(f"osc @ {ts}: addr={addr} msg={str(params)}")

    def stop(self) -> None:
        """Do everything needed to stop the server."""
        logger.debug(f"Stopping {__class__.__name__}")

        if hasattr(self, "vrcOscConnector"):
            self.vrcOscConnector.close()

        if hasattr(self, "hwManager"):
            self.hwManager.close()


if __name__ == "__main__":
    print("There is no point running this file directly")
