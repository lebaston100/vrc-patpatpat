from PyQt6.QtCore import QObject


class ESP(QObject):
    """Represents a physical ESP"""

    def __init__(self, key: str, settings: dict, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._key = key
        self._id: int = settings["id"]
        self._name: str = settings["name"]
        self._lastIp: str = settings["lastIp"]
        self._wifiMac: str = settings["wifiMac"]
        self._numMotors: int = settings["numMotors"]
