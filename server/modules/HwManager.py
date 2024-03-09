"""This module handles all the communication with the hardware devices
including discovery
"""

import socket

from PyQt6.QtCore import QObject, QThread, QTimer
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from modules.GlobalConfig import GlobalConfigSingleton
from modules.HardwareDevice import HardwareDevice
from modules.OscMessageTypes import DiscoveryResponseMessage, HeartbeatMessage
from utils.Enums import HardwareConnectionType
from utils.Logger import LoggerClass
from utils.threadToStr import threadAsStr

logger = LoggerClass.getSubLogger(__name__)
config = GlobalConfigSingleton.getInstance()


class HwManager(QObject):
    """Handles all hardware related tasks."""

    hwListChanged = QSignal(dict)
    _hwConfigChanged = QSignal(str)
    _hwConfigRemoved = QSignal(str)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)
        self._configKey = "esps"

        self.hardwareDevices: dict[int, HardwareDevice] = {}

        # Start osc receiver for discovery and heartbeat
        self.hwOscRx = HwOscRx()
        self.hwOscRx.onDiscoveryResponseMessage.connect(
            self._handleDiscoveryResponseMessage)

        self.hwOscDiscoveryTx: HwOscDiscoveryTx | None = None
        self._handleProgramConfigChange("program.enableOscDiscovery")

        config.configPathHasChanged.connect(self._handleProgramConfigChange)
        config.registerChangeSignal(
            r"esps\..*", self._hwConfigChanged)
        self._hwConfigChanged.connect(self._handleConfigChange)
        config.registerRemoveSignal(
            r"esps\..*", self._hwConfigRemoved)
        self._hwConfigRemoved.connect(self._handleConfigRemoved)

    def writeSpeed(self, hwId: int = 0, channelId: int = 0,
                   value: float | int = 0) -> None:
        """Write speed from motor into HardwareDevice's state buffer

        Args:
            hwId (int, optional): The destined HardwareDevice.
                Defaults to 0.
            channelId (int, optional): The destined HardwareDevice's
                channel. Defaults to 0.
            value (float | int, optional): The value to write.
                Defaults to 0.
        """
        # logger.debug(f"writeSpeed({hwId}, {channelId}, {value})")
        if hwId in self.hardwareDevices \
                and channelId in self.hardwareDevices[hwId].pinStates:
            self.hardwareDevices[hwId].pinStates[channelId] = value
        else:
            logger.debug("Specified HardwareDevice does not exist")

    def sendHwUpdateForId(self, hwId: int = 0) -> None:
        """Triggers a sendPinValues() on the destined Hardware.

        Args:
            hwId (int): Id of the destined HardwareDevice.
                Defaults to 0.
        """
        if hwId in self.hardwareDevices:
            self.hardwareDevices[hwId].sendPinValues()
        else:
            logger.debug("Specified HardwareDevice does not exist")

    def sendHwUpdate(self) -> None:
        """Triggers a sendPinValues() on all hardware."""
        for device in self.hardwareDevices.values():
            device.sendPinValues()

    def createAllHardwareDevicesFromConfig(self) -> None:
        """Creates all HardwareDevice objects from the config file."""
        logger.debug("(Re-)creating all HardwareDevice objects")
        devices = config.get(self._configKey)
        for key, device in devices.items():
            newDevice = self._deviceFactory(key)
            self.hardwareDevices[device["id"]] = newDevice
        self.hwListChanged.emit(self.hardwareDevices)

    @QSlot(str)
    def _handleConfigChange(self, key: str) -> None:
        """Handle config change events.
        (Re-)creates the HardwareDevice objects as needed

        Args:
            key (str): The key of the config parameter that was changed.
        """
        if key.startswith(f"{self._configKey}.esp"):
            keys = key.split(".")
            id = config.get(f"{".".join(keys[:2])}.id")
            if id in self.hardwareDevices:
                # The device already exits, close first
                self.hardwareDevices[id].close()
            self.hardwareDevices[id] = self._deviceFactory(keys[1])
            self.hwListChanged.emit(self.hardwareDevices)

    def _handleConfigRemoved(self, path: str) -> None:
        if path.startswith("esps.esp"):
            deviceId = int(path.removeprefix("esps.esp"))
            self.hardwareDevices[deviceId].close()
            del self.hardwareDevices[deviceId]
            self.hwListChanged.emit(self.hardwareDevices)

    def _handleProgramConfigChange(self, path: str) -> None:
        if path == "program.enableOscDiscovery":
            """Handle start/stop of the osc discovery sender"""
            if config.get("program.enableOscDiscovery"):
                if hasattr(self, "hwOscDiscoveryTx") \
                        and self.hwOscDiscoveryTx:
                    self.hwOscDiscoveryTx.stop()
                    self.hwOscDiscoveryTx = None
                self.hwOscDiscoveryTx = HwOscDiscoveryTx()
                self.hwOscDiscoveryTx.start()
            elif hasattr(self, "hwOscDiscoveryTx") and self.hwOscDiscoveryTx:
                self.hwOscDiscoveryTx.stop()
                self.hwOscDiscoveryTx = None

    def _deviceFactory(self, key: str) -> HardwareDevice:
        """Creates a new device given it's config key.

        Args:
            key (str): The config key. Eg "esp0"

        Returns:
            HardwareDevice: The new HardwareDevice instance
        """
        device = HardwareDevice(key)
        self.hwOscRx.onOscHeartbeatMessage.connect(
            device.hardwareCommunicationAdapter.receivedExtHeartbeat)
        return device

    def _handleDiscoveryResponseMessage(self, msg: DiscoveryResponseMessage) -> None:
        """Handle discovery response messages.

        If the device already exists, it returns. If not, it creates a new
        device from scratch.

        Args:
            msg (DiscoveryResponseMessage): The discovery response message.
        """
        # Check if device already exists and return if it does so
        if (id := self._checkDeviceExistance(msg.mac)) is not None:
            logger.debug(f"Device with mac {msg.mac} already exists in config "
                         f"as id {id} . Not creating a new one.")
            self.hardwareDevices[id].wasDiscovered = True
            return
        # If not this means it's a brand new device, create from scratch
        # Get a new device id
        newDeviceId = self._getNewHardwareId()
        newDeviceKey = f"esp{newDeviceId}"
        # Create config object with initial values
        newDeviceData = {
            "id": newDeviceId,
            "name": msg.hostname,
            "connectionType": msg.sourceType,
            "lastIp": msg.sourceAddr if
            msg.sourceType == HardwareConnectionType.OSC else "",
            "wifiMac": msg.mac,
            "serialPort": msg.sourceAddr if
            msg.sourceType == HardwareConnectionType.SLIPSERIAL else "",
            "numMotors": msg.numMotors
        }
        # Save new device to config
        config.set(f"esps.{newDeviceKey}", newDeviceData, wasChanged=True)
        # handle device "re"-creation through existing config change signal

    def createEmptyDevice(self) -> None:
        newDeviceId = self._getNewHardwareId()
        newDeviceKey = f"esp{newDeviceId}"
        # Create config object with initial values
        newDeviceData = {
            "id": newDeviceId,
            "name": f"Unnamed Hardware {newDeviceId}",
            "connectionType": HardwareConnectionType.OSC,
            "lastIp": "169.254.1.50",
            "wifiMac": "FF:FF:FF:FF:FF:FF",
            "serialPort": "",
            "numMotors": 1
        }
        # Save new device to config
        config.set(f"esps.{newDeviceKey}", newDeviceData, wasChanged=True)
        # handle device "re"-creation through existing config change signal

    def _checkDeviceExistance(self, mac: str) -> int | None:
        """Checks config if given mac adress already exists.

        Args:
            mac (str): The mac adress to look for

        Returns:
            int | None: If mac is found in config, it's id, otherwise None
        """
        hardwareDevices: dict = config.get("esps")
        return next((device["id"] for device in hardwareDevices.values()
                     if device["wifiMac"] == mac), None)

    def _getNewHardwareId(self) -> int:
        """Calculates an available index for a new device

        Returns:
            int: The new device index
        """
        if hardwareDevices := config.get("esps"):
            return max([d["id"] for d in hardwareDevices.values()]) + 1
        return 0

    def close(self) -> None:
        """Closes everything hardware related."""
        logger.debug(f"Stopping {__class__.__name__}")
        if hasattr(self, "hwOscDiscoveryTx") and self.hwOscDiscoveryTx:
            self.hwOscDiscoveryTx.stop()
        if hasattr(self, "hwOscRx"):
            self.hwOscRx.close()

        for device in self.hardwareDevices.values():
            device.close()


class HwOscDiscoveryTx(QObject):
    """Sends out hardware discovery broadcasts on all interfaces
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initializes the HwOscDiscoveryTx object.
        """
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._interfaces = socket.getaddrinfo(
            host=socket.gethostname(), port=None, family=socket.AF_INET)
        self._sockets: list[SimpleUDPClient] = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.timerEvent)

    def start(self, interval: int = 3) -> None:
        """Starts the timer with the specified interval.

        Args:
            interval: The interval in seconds. Default is 3.
        """
        self._interval = interval
        if self._timer.isActive():
            self.stop()

        # We have no idea about the actual netmask, so 255... it is
        for interface in self._interfaces:
            client = SimpleUDPClient(
                "255.255.255.255", 8888,
                allow_broadcast=True, family=socket.AF_INET)
            client._sock.bind((interface[-1][0], 8871))
            self._sockets.append(client)
        self.timerEvent()
        self._timer.start(self._interval*1000)

    def stop(self) -> None:
        """Stops the timer and closes all sockets."""
        logger.debug(f"Stopping {__class__.__name__}")
        for client in self._sockets:
            client._sock.shutdown(socket.SHUT_RDWR)
            client._sock.close()
        self._sockets = []
        self._timer.stop()

    @QSlot()
    def timerEvent(self) -> None:
        """Send out discovery messages when timer fires."""
        # logger.debug("Sending out discovery broadcasts")
        for client in self._sockets:
            client.send_message("/patpatpat/discover", [])


class HwOscRxWorker(QObject):
    """The thread receiving osc messages from hardware devices."""

    onDiscoveryResponseMessage = QSignal(object)
    onOscHeartbeatMessage = QSignal(object)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.dispatcher = Dispatcher()
        self.dispatcher.map("/patpatpat/noticeme/senpai",
                            self._handleDiscoveryResponseMessage,
                            needs_reply_address=True)
        self.dispatcher.map("/patpatpat/heartbeat",
                            self._handleHeartbeatMessage,
                            needs_reply_address=True)
        self.dispatcher.set_default_handler(self._defaultHandler)

    def _defaultHandler(self, topic: str, *args) -> None:
        logger.debug(f"Unknown osc message: {topic}, {str(args)}")

    def _handleDiscoveryResponseMessage(self, client: tuple,
                                        topic: str, *args) -> None:
        # logger.debug(f"_handleDiscoveryResponseMessage: {str(client)}, {topic}, {str(args)}")
        if DiscoveryResponseMessage.isType(topic, args):
            msg = DiscoveryResponseMessage(
                *args, sourceType=HardwareConnectionType.OSC, sourceAddr=client[0])
            logger.debug(msg)
            self.onDiscoveryResponseMessage.emit(msg)

    def _handleHeartbeatMessage(self, client: tuple,
                                topic: str, *args) -> None:
        # logger.debug(f"_handleHeartbeatMessage: {str(client)}, {topic}, {str(args)}")
        if HeartbeatMessage.isType(topic, args):
            msg = HeartbeatMessage(*args, sourceAddr=client[0])
            # logger.debug(msg)
            self.onOscHeartbeatMessage.emit(msg)

    @QSlot()
    def startOscServer(self) -> None:
        logger.debug(
            f"startOsc pid     ={threadAsStr(QThread.currentThread())}")
        logger.debug(
            f"startOsc pid_self={threadAsStr(self.thread())}")
        logger.info(f"Starting osc server on port 8872")
        try:
            self._oscRx = BlockingOSCUDPServer(("", 8872), self.dispatcher)
            self._oscRx.serve_forever()
        except Exception as E:
            logger.exception(E)
        logger.debug("startOscServer done, cleaning up...")
        self._oscRx.socket.close()
        del self._oscRx  # dereferene so the gc can pick it up

    def closeOscServer(self) -> None:
        """Stops and closes the osc server."""

        logger.debug(f"closeOscServer in {__class__.__name__}")
        selfThread = self.thread()
        logger.debug(f"pid_QThread.currentThread={threadAsStr(QThread.currentThread())} "
                     f"pid_selfThread={threadAsStr(selfThread)} ")
        if hasattr(self, "_oscRx"):
            self._oscRx.shutdown()
        if selfThread:
            selfThread.quit()
            selfThread.wait()


class HwOscRx(QObject):
    """The Thread Manager for the global Hardware Osc Receiver."""

    onDiscoveryResponseMessage = QSignal(object)
    onOscHeartbeatMessage = QSignal(object)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.worker = HwOscRxWorker()
        self.workerThread = QThread()
        self.workerThread.started.connect(self.worker.startOscServer)
        self.worker.moveToThread(self.workerThread)

        # relay signals
        self.worker.onDiscoveryResponseMessage.connect(
            self.onDiscoveryResponseMessage)
        self.worker.onOscHeartbeatMessage.connect(
            self.onOscHeartbeatMessage)

        logger.debug("Starting heartbeat osc server and client")
        self.workerThread.start(QThread.Priority.HighestPriority)

    def close(self) -> None:
        """Closes everything heartbeat osc related."""
        logger.debug("Closing heartbeat osc")
        self.worker.closeOscServer()
        self.workerThread.quit()
        self.workerThread.wait()


if __name__ == "__main__":
    print("There is no point running this file directly")
