from typing import TypeVar

from PyQt6.QtCore import QObject, QThread

from modules import config
from modules.ContactGroup import ContactGroupManager
from modules.HwManager import HwManager
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

        self.hwManager = HwManager()

        self.contactGroupManager = ContactGroupManager()

        self.vrcOscConnector.onVrcContact.connect(
            self.contactGroupManager.onVrcContact)
        self.contactGroupManager.registerAvatarPoint.connect(
            self.vrcOscConnector.addToFilter)
        self.contactGroupManager.unregisterAvatarPoint.connect(
            self.vrcOscConnector.removeFromFilter)
        self.contactGroupManager.motorPwmChanged.connect(
            self.hwManager.writeSpeed)
        self.contactGroupManager.solverDone.connect(
            self.hwManager.sendHwUpdate)

        self.hwManager.createAllHardwareDevicesFromConfig()
        self.contactGroupManager.createAllContactGroupsFromConfig()

        ServerSingleton.__instance = self

    def stop(self) -> None:
        """Do everything needed to stop the server."""
        logger.debug(f"Stopping {__class__.__name__}")

        if hasattr(self, "contactGroupManager"):
            self.contactGroupManager.close()

        if hasattr(self, "vrcOscConnector"):
            self.vrcOscConnector.close()

        if hasattr(self, "hwManager"):
            self.hwManager.close()


if __name__ == "__main__":
    print("There is no point running this file directly")
