from PyQt6.QtCore import QObject
from modules.GlobalConfig import GlobalConfigSingleton


class HardwareDevice(QObject):
    """Represents a physical ESP"""

    def __init__(self, key: str) -> None:
        super().__init__()
        self._key = key
        self._configKey = f"esps.{self._key}"
        self._isConnected = False

    def loadSettings(self, config: GlobalConfigSingleton):
        self._id: int = config.get(f"{self._configKey}.id")
        self._name: str = config.get(f"{self._configKey}.name", "")
        self._lastIp: str = config.get(f"{self._configKey}.lastIp")
        self._wifiMac: str = config.get(f"{self._configKey}.wifiMac")
        self._numMotors: int = config.get(f"{self._configKey}.numMotors", 0)

    # def writeSettings(self, config: GlobalConfigSingleton):
        # config.set(f"{self._configKey}.lastIp", self._lastIp, True)
