import socket
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from pythonosc.udp_client import SimpleUDPClient

from modules.GlobalConfig import config
from modules.OscMessageTypes import HeartbeatMessage
from utils import HardwareConnectionType, LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class HardwareDevice(QObject):
    """Represents a physical Hardware Device/ESP."""

    uiBatteryStateChanged = QSignal(float)
    uiRssiStateChanged = QSignal(int)
    deviceConnectionChanged = QSignal(bool)
    motorDataSent = QSignal(list)

    def __init__(self, key: str) -> None:
        super().__init__()
        self._configKey = f"esps.{key}"
        self.wasDiscovered = False

        # Heartbeat checker
        self.currentConnectionState: bool = False
        self._lastHeartbeat: HeartbeatMessage | None = None
        self._heartbeatTimer = QTimer()
        self._heartbeatTimer.timeout.connect(self.updateConnectionStatus)
        self._heartbeatTimer.start(9000)

        self._loadSettingsFromConfig()
        self.pinStates: dict[int, int | float] = {
            i: 0 for i in range(self._numMotors)}
        hardwareCommunicationAdapterClass = \
            HardwareCommunicationAdapterFactory.build_adapter(
                self._connectionType)
        if hardwareCommunicationAdapterClass:
            self.hardwareCommunicationAdapter = \
                hardwareCommunicationAdapterClass()
        else:
            raise RuntimeError("Unknown hardware connection type.")
        self.hardwareCommunicationAdapter.setup(config.get(self._configKey))

        self.hardwareCommunicationAdapter.heartbeat.connect(
            self.processHeartbeat)

    def _loadSettingsFromConfig(self) -> None:
        """Load settings from settings file into object."""
        self._id: int = config.get(f"{self._configKey}.id")
        self._name: str = config.get(f"{self._configKey}.name", "")
        self._connectionType: int = config.get(
            f"{self._configKey}.connectionType", "OSC")
        self._lastIp: str = config.get(f"{self._configKey}.lastIp")
        self._wifiMac: str = config.get(f"{self._configKey}.wifiMac")
        self._serialPort: str = config.get(f"{self._configKey}.serialPort", "")
        self._numMotors: int = config.get(f"{self._configKey}.numMotors", 0)

    @QSlot()
    def resetAllPinStates(self) -> None:
        """Set all channels to 0 and send update to hardware."""
        self.pinStates = {i: 0 for i in range(self._numMotors)}
        self.sendPinValues()

    @QSlot(int, int)
    def setAndSendPinValues(self, channelId: int, value: int) -> None:
        """Set a channel to a value and send update to hardware.

        Args:
            channelId (int): The channel to set the value for
            value (int): The new PWM value
        """
        self.pinStates[channelId] = value
        self.sendPinValues()

    def sendPinValues(self) -> None:
        """Create and send current self.pinStates to hardware."""
        motorData = list(self.pinStates.values())[:self._numMotors]
        self.hardwareCommunicationAdapter.sendPinValues(motorData)
        self.motorDataSent.emit(motorData)

    def processHeartbeat(self, msg: HeartbeatMessage) -> None:
        """Process an incoming heartbeat message from the comms interface.

        Args:
            msg (HeartbeatMessage): The HeartbeatMessage dataclass
        """
        # Check if this message belongs to us
        if not msg.mac == self._wifiMac:
            return
        self._lastHeartbeat = msg
        # Check if the ip addr changed from known config
        if not msg.sourceAddr == self._lastIp:
            logger.debug(f"Device {self._name} changed ip from "
                         f"{self._lastIp} to {msg.sourceAddr}")
            config.set(f"{self._configKey}.lastIp", msg.sourceAddr, True)
            return
        self.uiBatteryStateChanged.emit(msg.vccBat)
        self.uiRssiStateChanged.emit(msg.rssi)
        self.updateConnectionStatus()

    @QSlot()
    def updateConnectionStatus(self) -> None:
        """Recalculate the hardware connection status."""
        # NOTE: This might need some rework some time
        if not self._lastHeartbeat:
            return
        # logger.debug(datetime.now())
        # logger.debug(self._lastHeartbeat.ts.second)
        # logger.debug((datetime.now() - self._lastHeartbeat.ts).total_seconds())
        if not self.currentConnectionState and \
                (datetime.now() - self._lastHeartbeat.ts).total_seconds() <= 6:
            self.currentConnectionState = True
            logger.debug(f"hw connection state for device {self._id} changed to"
                         f" {self.currentConnectionState}")
            self.deviceConnectionChanged.emit(self.currentConnectionState)
        elif self.currentConnectionState and \
                (datetime.now() - self._lastHeartbeat.ts).total_seconds() > 6:
            self.currentConnectionState = False
            logger.debug(f"hw connection state for device {self._id} changed to"
                         f" {self.currentConnectionState}")
            self.deviceConnectionChanged.emit(self.currentConnectionState)

    def close(self) -> None:
        """Closes everything we own and care for."""
        logger.debug(f"Stopping {__class__.__name__}({self._id})")
        if hasattr(self, "_heartbeatTimer") and self._heartbeatTimer.isActive():
            self._heartbeatTimer.stop()
        if hasattr(self, "hardwareCommunicationAdapter"):
            self.hardwareCommunicationAdapter.close()

    def __repr__(self) -> str:
        return f"{__class__.__name__}(id={self._id}, name='{self._name}', " \
            f"connectionType='{self._connectionType}', " \
            f"ip='{self._lastIp}', mac='{self._wifiMac}' "\
            f"serialPort='{self._serialPort}', numMotors={self._numMotors})"


class IHardwareCommunicationAdapter():
    """The interface for a HardwareDevice to talk to the actual hardware."""

    heartbeat = QSignal(object)

    def setup(self, settings: dict) -> None:
        """A generic setup method to be reimplemented."""
        raise NotImplementedError

    def sendPinValues(self, pinValues: list) -> None:
        """A generic sendPinValues method to be reimplemented."""
        raise NotImplementedError

    def receivedExtHeartbeat(self, msg: HeartbeatMessage) -> None:
        """A generic receivedExtHeartbeat method to be reimplemented."""
        raise NotImplementedError

    def close(self) -> None:
        """A generic close method to be reimplemented."""
        raise NotImplementedError


class OscCommunicationAdapterImpl(IHardwareCommunicationAdapter, QObject):
    """Handle communication with a device over OSC."""

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._oscClient: SimpleUDPClient | None = None

    def setup(self, settings: dict) -> None:
        """Setup everything required for this communication
        interface to work.

        Args:
            settings (dict): The settings dict for this esp
        """
        try:
            self.close()
            self._oscClient = SimpleUDPClient(settings["lastIp"], 8888)
        except Exception as E:
            logger.exception(E)

    def sendPinValues(self, pinValues: list) -> None:
        """Send motor values to device over osc."""
        # TODO: Inspect exception behaviour and add catch if needed
        if self._oscClient:
            self._oscClient.send_message("/m", pinValues)

    @QSlot(object)
    def receivedExtHeartbeat(self, msg: HeartbeatMessage) -> None:
        """Re-emit the heartbeat message so the interfacce is consistant.

        Args:
            msg (HeartbeatMessage): The HeartbeatMessage dataclass instance
        """
        self.heartbeat.emit(msg)

    def close(self) -> None:
        """Do everything needed to cleanly close this class."""
        if self._oscClient:
            logger.debug(f"Stopping {__class__.__name__}")
            self._oscClient._sock.shutdown(socket.SHUT_RDWR)
            self._oscClient._sock.close()
            self._oscClient = None


class SlipSerialCommunicationAdapterImpl(IHardwareCommunicationAdapter, QObject):
    """Handle communication with a device over Serial."""

    def __init__(self, *args, **kwargs) -> None:
        ...

    def receivedExtHeartbeat(self, msg: HeartbeatMessage) -> None:
        """Not required for this connection type."""
        pass


class HardwareCommunicationAdapterFactory:
    """Factory class to build hardware communication adapters."""

    @staticmethod
    def build_adapter(adapterType) -> type[OscCommunicationAdapterImpl] | \
            type[SlipSerialCommunicationAdapterImpl] | None:
        """Static method to build the appropriate adapter based on the type.

        Args:
            adapterType (str): The type of adapter to build.

        Returns:
            type[OscCommunicationAdapterImpl] | 
                type[SlipSerialCommunicationAdapterImpl] |
                None: The built adapter or None if the type is not recognized.
        """
        match adapterType:
            case HardwareConnectionType.OSC:
                return OscCommunicationAdapterImpl
            case HardwareConnectionType.SLIPSERIAL:
                return SlipSerialCommunicationAdapterImpl


if __name__ == "__main__":
    print("There is no point running this file directly")
