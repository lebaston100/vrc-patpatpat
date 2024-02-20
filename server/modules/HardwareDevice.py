import socket

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from pythonosc.udp_client import SimpleUDPClient

from modules.GlobalConfig import GlobalConfigSingleton, config
from modules.OscMessageTypes import DiscoveryResponseMessage, HeartbeatMessage
from utils import LoggerClass, threadAsStr

logger = LoggerClass.getSubLogger(__name__)


class HardwareDevice(QObject):
    """Represents a physical Hardware Device/ESP."""

    frontendDataChanged = QSignal()
    motorDataSent = QSignal()  # Not sure about this yet
    deviceConnectionChanged = QSignal(bool)

    def __init__(self, key: str) -> None:
        super().__init__()
        self._configKey = f"esps.{key}"

        # Heartbeat checker
        self.connectionStatus: bool = False
        self._lastHeartbeat: None | HeartbeatMessage = None
        self._heartbeatTimer = QTimer()
        self._heartbeatTimer.timeout.connect(self.updateConnectionStatus)
        self._heartbeatTimer.start(10)

        self.loadSettingsFromConfig()
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

        self.hardwareCommunicationAdapter.heartbeat.connect(
            self.processHeartbeat)

    def loadSettingsFromConfig(self) -> None:
        """Load settings from settings file into object."""
        self._id: int = config.get(f"{self._configKey}.id")
        self._name: str = config.get(f"{self._configKey}.name", "")
        self._connectionType: int = config.get(
            f"{self._configKey}.connectionType", "OSC")
        self._lastIp: str = config.get(f"{self._configKey}.lastIp")
        self._wifiMac: str = config.get(f"{self._configKey}.wifiMac")
        self._serialPort: str = config.get(f"{self._configKey}.serialPort", "")
        self._numMotors: int = config.get(f"{self._configKey}.numMotors", 0)

    def sendPinValues(self) -> None:
        """Create and send current self.pinStates to hardare."""
        self.hardwareCommunicationAdapter.sendPinValues(
            list(self.pinStates.values())[:self._numMotors-1])

    def processHeartbeat(self, msg: HeartbeatMessage) -> None:
        """Process an incoming heartbeat message from the comms interface.

        Args:
            msg (HeartbeatMessage): The HeartbeatMessage dataclass
        """
        logger.debug("I've had a long journey, but now i'm finally here")
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
        self.updateConnectionStatus()

    def updateConnectionStatus(self) -> None:
        """Recalculate the hardware connection status."""
        currentConnectionStatus = False
        # TODO: Add actual calculations
        if not self.connectionStatus == currentConnectionStatus:
            # NOTE: connect straight to StatefulLabel.setState in UI
            self.deviceConnectionChanged.emit(self.connectionStatus)

    def close(self) -> None:
        """Closes everything we own and care for
        """
        logger.debug(f"Stopping {__class__.__name__}")
        self.frontendDataChanged.disconnect()
        self.motorDataSent.disconnect()
        self.deviceConnectionChanged.disconnect()
        if hasattr(self, "_heartbeatTimer") and self._heartbeatTimer.isActive():
            self._heartbeatTimer.stop()
        if hasattr(self, "hardwareCommunicationAdapter"):
            self.hardwareCommunicationAdapter.close()


class IHardwareCommunicationAdapter():
    """The interface for a HardwareDevice to talk to the actual hardware."""

    heartbeat = QSignal(object)

    def setup(self):
        """A generic setup method to be reimplemented."""
        raise NotImplementedError

    def sendPinValues(self, pinValues: list):
        """A generic sendPinValues method to be reimplemented."""
        raise NotImplementedError

    def receivedExtHeartbeat(self, msg: HeartbeatMessage):
        """A generic receivedExtHeartbeat method to be reimplemented."""
        raise NotImplementedError

    def close(self):
        """A generic close method to be reimplemented."""
        raise NotImplementedError


class OscCommunicationAdapterImpl(IHardwareCommunicationAdapter, QObject):
    """Handle communication with a device over OSC."""

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._oscClient: SimpleUDPClient | None = None

    def setup(self):
        """Setup everything required for this communication
        interface to work."""
        self._oscClient = SimpleUDPClient("ip", 8888)

    def sendPinValues(self, pinValues: list):
        """Send motor values to device over osc."""
        if self._oscClient:
            self._oscClient.send_message("/m", pinValues)

    def receivedExtHeartbeat(self, msg: HeartbeatMessage) -> None:
        """Re-emit the heartbeat message so the interfacce is consistant.

        Args:
            msg (HeartbeatMessage): The HeartbeatMessage dataclass instance
        """
        self.heartbeat.emit(msg)

    def close(self):
        """Do everything needed to cleanly close this class."""
        logger.debug(f"Stopping {__class__.__name__}")
        self.heartbeat.disconnect()
        if self._oscClient:
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
            case "OSC":
                return OscCommunicationAdapterImpl
            case "SlipSerial":
                return SlipSerialCommunicationAdapterImpl


if __name__ == "__main__":
    print("There is no point running this file directly")
