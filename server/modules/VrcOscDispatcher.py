"""
A drop-in replacement of the original osc dispatcher modified
to have less overhead to faster handle the data coming from vrc
"""

from PyQt6.QtCore import QThread
from pythonosc import osc_packet
from pythonosc.dispatcher import Dispatcher

from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class VrcOscDispatcher(Dispatcher):
    """A custom dispatcher for OSC messages.

    This class overwrites some functionalities in the OSC library to
    optimize the processing time of OSC messages. This is safe as the
    overwritten functionalities are not required in this case.

    Attributes:
        _server (OSCWorker): The OSC server.
    """

    def __init__(self, server) -> None:
        """Initializes the VrcOscDispatcher.

        The superclass's __init__ method is intentionally not called.

        Args:
            server (OSCWorker): The OSC server.
        """

        self._server = server
        # TODO: Wee need an additional list of topics to match from the config

    def call_handlers_for_packet(self, data: bytes,
                                 client_address: tuple[str, int]) -> None:
        """Handles incoming OSC packets.

        Parses the incoming OSC packet and emits a signal if the message
        address starts with "/avatar/parameters/". Logs a debug message
        for each incoming OSC message and if the OSC packet could not
        be parsed.

        Args:
            data (bytes): The incoming OSC packet data.
            client_address (tuple[str, int]): The client address.
        """

        try:
            packet = osc_packet.OscPacket(data)
            for msg in packet.messages:
                if msg.message.address[:19] == "/avatar/parameters/":
                    pid = str(int(QThread.currentThread().currentThreadId()))
                    logger.debug(
                        f"pid={pid} incoming osc from {client_address}: "
                        f"addr={msg.message.address} "
                        f"msg={str(msg.message.params)}"
                    )
                    self._server.gotVrcContact.emit(
                        client_address,
                        msg.message.address,
                        msg.message.params
                    )
        except osc_packet.ParseError:
            logger.debug("Could not parse osc message")
