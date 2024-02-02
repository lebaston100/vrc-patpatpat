from typing import Type, TypeVar

from PyQt6.QtCore import QObject, QThread

from utils import LoggerClass, threadAsStr
from modules.Solver import SolverRunner
from modules import config
from modules.VrcConnector import VrcConnectorImpl

logger = LoggerClass.getSubLogger(__name__)

T = TypeVar('T', bound='ServerSingleton')


class ServerSingleton(QObject):
    __instance = None

    @classmethod
    def getInstance(cls: Type[T]) -> T:
        """
        Get the singleton instance.

        Returns:
            ServerSingleton: Singleton instance.
        """

        return cls.__instance

    def __init__(self, *args, **kwargs) -> None:

        if ServerSingleton.__instance:
            raise RuntimeError("Can't initialize multiple singleton instances")

        super().__init__()
        logger.debug(f"Creating {__class__.__name__} in thread {
                     threadAsStr(QThread.currentThread())} ")

        self.vrcOscConnector = VrcConnectorImpl(config)
        self.vrcOscConnector.connect()
        # self.vrcOscConnector.addToFilter("pat_2")

        self._solverRunnerThread = QThread()
        self.solverRunner = SolverRunner(config)

        # self._solverRunnerThread.started.connect(self.solverRunner.runSolvers)
        # self.solverRunner.moveToThread(self._solverRunnerThread)
        # self._solverRunnerThread.start()

        ServerSingleton.__instance = self

    def stop(self):
        """Do everything needed to stop the server
        """
        if hasattr(self, "vrcOscConnector"):
            self.vrcOscConnector.close()


if __name__ == "__main__":
    print("There is no point running this file directly")
