from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot

from modules import config
from modules.GlobalConfig import GlobalConfigSingleton
from modules.OscMessageTypes import DiscoveryResponseMessage, HeartbeatMessage
from utils import LoggerClass, threadAsStr

logger = LoggerClass.getSubLogger(__name__)


class HardwareDevice(QObject):
    """Represents a physical Hardware Device/ESP"""

    frontendDataChanged = QSignal()
    motorDataSent = QSignal()  # Not sure about this yet
    deviceConnectionChanged = QSignal(bool)

    def __init__(self, key: str) -> None:
        super().__init__()
        self._configKey = f"esps.{key}"
        self._isConnected = False
        self._lastHeartbeat: None | HeartbeatMessage = None
        self._heartbeatTimer = QTimer()
        self.loadSettingsFromConfig()
        self.pinStates: dict[int, int | float] = {
            i: 0 for i in range(self._numMotors)}
        # self.hardwareCommunicationAdapter = IHardwareCommunicationAdapter

    def loadSettingsFromConfig(self) -> None:
        """Load settings from settings file into object
        """
        self._id: int = config.get(f"{self._configKey}.id")
        self._name: str = config.get(f"{self._configKey}.name", "")
        self._connectionType: int = config.get(
            f"{self._configKey}.connectionType", "osc")
        self._lastIp: str = config.get(f"{self._configKey}.lastIp")
        self._wifiMac: str = config.get(f"{self._configKey}.wifiMac")
        self._serialPort: str = config.get(f"{self._configKey}.serialPort", "")
        self._numMotors: int = config.get(f"{self._configKey}.numMotors", 0)

    def sendPinValues(self) -> None:
        """Create and send current self.pinStates to Hw
        """
        ...

    def processHeartbeat(self, msg: HeartbeatMessage) -> None:
        """Process an incoming heartbeat message from the comms interface

        Args:
            msg (HeartbeatMessage): The HeartbeatMessage dataclass
        """
        ...

    def updateConnectionStatus(self) -> None:
        """Recalculate the hardware connection status
        """
        ...
        # self.deviceConnectionChanged.emit(self._isConnected)

    def close(self) -> None:
        """Closes everything we own and care for
        """

        logger.debug(f"Stopping {__class__.__name__}")
        if hasattr(self, "hwOscDiscoveryTx") and self._heartbeatTimer.isActive():
            self._heartbeatTimer.stop()

# TODO: Add factory for HardwareCommunicationAdapter


class IHardwareCommunicationAdapter():
    """The interface for a HardwareDevice to talk to the actual hardware"""

    heartbeat = QSignal(object)

    def setup(self):
        """ A generic setup method to be reimplemented"""
        raise NotImplementedError

    def sendPinValues(self):
        """ A generic sendPinValues method to be reimplemented"""
        raise NotImplementedError

    def receivedExtHeartbeat(self):
        """ A generic receivedExtHeartbeat method to be reimplemented"""
        raise NotImplementedError

    def close(self):
        """ A generic close method to be reimplemented"""
        raise NotImplementedError


class OscCommunicationAdapterImpl(IHardwareCommunicationAdapter, QObject):
    """Handle communication with a device over OSC
    """

    def __init__(self, *args, **kwargs) -> None:
        ...


class SlipSerialCommunicationAdapterImpl(IHardwareCommunicationAdapter, QObject):
    """Handle communication with a device over Serial
    """

    def __init__(self, *args, **kwargs) -> None:
        ...
