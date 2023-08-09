from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt
from PyQt6.QtDataVisualization import Q3DScatter, QScatter3DSeries, QScatterDataProxy, QScatterDataItem
from PyQt6.QtGui import QVector3D, QColorConstants
from zeroconf import Zeroconf
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
import paho.mqtt.client as mqtt
from multilateration import Engine
from multilateration import Point as mlatPoint
from typing import Union

# for docstrings and typing
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from config import Config

import threading
import socket
import time
import logging

class Server():
    def __init__(self, window):
        self.window = window
        self.config: Config = window.config
        self.running = True
        self.oscTx = None
        self.mqtt = None
        self._resetValues()
        # run hardware discovery in seperate thread to not wait for it
        threading.Thread(target=self._discoverHardware, args=()).start()

        # vrchat and patpatpat osc receiver
        threading.Thread(target=self._OscReceiverThread, args=()).start()

        # the "game loop" aka calculate stuff and send to hardware
        threading.Thread(target=self._mainLoopThread, args=()).start()

        # mqtt control interface (might expand or remove in the future)
        threading.Thread(target=self._MqttReceiverThread, args=()).start()

    def _resetValues(self) -> None:
        """Initialize some internal values"""
        self.vrc_last_packet = self.patpatpat_last_heartbeat = time.time()-5
        self.enableVrcTx = True
        self.battery = 0
        self.numMotors = self.config.get("numMotors", 2)
        self.oscMotorTxData = [0]*self.numMotors
        self.patpatpatIsConnected = False
        self.vrcInValues = {k: {"v": 0, "ts": 0} for k in range(4)}
        # at some point change this to be a single dict each with the QVector3D and leftover data
        self.avatarAnchorPoints = [self.config.get(f"avatarPoint{avatarPointId}") for avatarPointId in range(4)]
        self.avatarPointsAsQVector3D = [QVector3D(p["x"], p["y"], p["z"]) for p in self.avatarAnchorPoints]
        self.motorPositions = [self.config.get(f"motor{motorPointId}") for motorPointId in range(self.numMotors)]
        self.motorPositionsAsQVector3D = [QVector3D(m["x"], m["y"], m["z"]) for m in self.motorPositions]
        # Show avatar points in visualizer
        self.window.visualizerPlot.addSeries(self._generateAvatarPointSeries([QScatterDataItem(p) for p in self.avatarPointsAsQVector3D]))
        self._generateCalculatedPointSeries()

    def _generateAvatarPointSeries(self, data) -> QScatter3DSeries:
        """A scatter serie to display the contact receiver positions"""
        proxy = QScatterDataProxy()
        proxy.addItems(data)
        series = QScatter3DSeries()
        series.setItemSize(0.1)
        series.setBaseColor(QColorConstants.Yellow)
        series.setDataProxy(proxy)
        return series

    def _generateCalculatedPointSeries(self) -> None:
        """A scatter series to hold the calculated 3d positions"""
        resultProxy = QScatterDataProxy()
        resultSeries = QScatter3DSeries()
        resultSeries.setItemSize(0.05)
        resultSeries.setBaseColor(QColorConstants.Red)
        resultSeries.setDataProxy(resultProxy)
        self.window.visualizerPlot.addSeries(resultSeries)

    def _checkMdnsServices(self) -> tuple[str, int]:
        """Run MDNS discovery and look for our hardware"""
        info = None
        self.zc = Zeroconf()
        while not info and self.running:
            info = self.zc.get_service_info("_osc._udp.local.", "patpatpat._osc._udp.local.", timeout=1500)
            time.sleep(0.1)
        if info:
            return (socket.inet_ntoa(info.addresses[0]), info.port)
        return (None, None)

    def _discoverHardware(self) -> bool:
        ip_address, port = self._checkMdnsServices()

        if ip_address is None or port is None:
            return

        logging.info(f"patpatpat found {ip_address} on port {port}")
        self.oscTx = SimpleUDPClient(ip_address, port)

    def _validateIncomingDataAge(self, d: dict) -> bool:
        """Check that all received points are fresh"""
        maxAge = time.time()-0.15 # this needs to be lower, not sure how fast vrc network sync is yet
        return all(e["ts"] > maxAge for e in d.values())

    def _calculateMlatPosition(self, distances: dict, anchorpoints: list[QVector3D]) -> Union[QVector3D, None]:
        """Calculate the 3d point"""
        if self._validateIncomingDataAge(distances):
            # run a mlat solver over the anchor points and the reported distances
            solver = Engine()
            for id, point in enumerate(anchorpoints):
                solver.add_anchor(f"anchor_{id}", (point.x(), point.y(), point.z()))
                solver.add_measure_id(f"anchor_{id}", distances[id]["v"])

            if result := solver.solve():
                return QVector3D(result.x, result.y, result.z)
        return None

    def _validateMlatPoint(self, point: QVector3D, center: QVector3D, centerRadius: float) -> bool:
        """Validate that the calculcated point makes sense"""
        # Distance from center point to calculcated point <= center radius + some margin
        return center.distanceToPoint(point) <= centerRadius*1.2

    # we need a gui function to update the 3d visualizer

    def _mainLoop(self):
        if self.oscTx == None:
            return

        # calculate the 3d position from the input data
        if pos := self._calculateMlatPosition(self.vrcInValues, self.avatarPointsAsQVector3D):
            if not self._validateMlatPoint(pos, self.avatarPointsAsQVector3D[0], self.avatarAnchorPoints[0]["r"]):
                return
            
            # we got a position from our calculations back
            logging.debug(pos)
            # add to visualizer
            # TODO: Cleanup
            if len(self.window.visualizerPlot.seriesList()[1].dataProxy().array()) > 150:
                self.window.visualizerPlot.seriesList()[1].dataProxy().removeItems(0, 1) # create trail
            self.window.visualizerPlot.seriesList()[1].dataProxy().addItem(QScatterDataItem(pos))

        # project 3d point onto motor sphere
        # TODO: is this actually needed. why don't we just calculate the distance between the touch point and motor positions, it has to be 3d anyway?
        # might save a bunch of calulcations

        #intensity = self.window.get_intensity() # this gets the slider setting, ignore for now

        if self.enableVrcTx:
            # Only send data here
            # send out motor speeds
            self.oscTx.send_message("/m", self.oscMotorTxData)        

    def _mainLoopThread(self, tps: int=60) -> None:

        # add some static points just for axis scaling
        self.window.visualizerPlot.seriesList()[0].dataProxy().addItems([QScatterDataItem(QVector3D(-0.5,-0.5,-0.5)),QScatterDataItem(QVector3D(0.5,0.5,0.5))])

        while self.running:
            loopStart = time.perf_counter_ns()
            
            # run actual calulcations in different function so we can just early return without messing up the performance counter
            self._mainLoop()

            # update gui connection status with a 2 seconds timeout
            # once i learn qt signals maybe this can be event based?
            self.window.setGuiVrcRecvStatus(self.vrc_last_packet+1 >= time.time())
            self.patpatpatIsConnected = self.patpatpat_last_heartbeat+2 >= time.time()
            self.window.setGuiHardwareConnectionStatus(self.patpatpatIsConnected)

            # calculate loop time
            loopEnd = time.perf_counter_ns()
            logging.debug(f"loop time: {(loopEnd-loopStart)/1000000}ms")
            #self._mqtt_send("dev/patpatpat/out/loopperf", (loopEnd-loopStart)/1000000)
            time.sleep(max((1/tps)-(loopEnd-loopStart)/1000000000, 0))

        logging.info("Exiting Application...")

    # handle vrchat osc receiving
    def _OscReceiverThread(self) -> None:
        # handle incoming vrchat osc messages
        def _recv_contact(address, cid, val) -> None:
            #logging.debug(f"cid {cid[0]} {address}: {val}")
            # invert value and scale it according to the colliders size
            scaledval = (1.0-val)*self.avatarAnchorPoints[cid[0]]["r"]
            self.vrcInValues[cid[0]] = {"v": scaledval, "ts": time.time()}
            self.vrc_last_packet = time.time()

        def _recv_patpatpat_heartbeat(_, mac, uptime, voltage, rssi) -> None:
            #logging.debug(f"Received patpatpat heartbeat from mac {mac} with uptime {uptime}s and voltage {voltage}mV and wifi rssi {rssi}dBm")
            self._mqttPublish("dev/patpatpat/out/heartbeat", uptime)
            self.patpatpat_last_heartbeat = time.time()

            # for now this is just the raw value, we later need to do some light processing to it
            self.battery = int(voltage)
            self.window.setGuiBattery(self.battery)

        # register required osc endpoints
        dispatcher = Dispatcher()
        dispatcher.map("/avatar/parameters/pat_center", _recv_contact, 0)
        dispatcher.map("/avatar/parameters/pat_1", _recv_contact, 1)
        dispatcher.map("/avatar/parameters/pat_2", _recv_contact, 2)
        dispatcher.map("/avatar/parameters/pat_3", _recv_contact, 3)
        dispatcher.map("/patpatpat/heartbeat", _recv_patpatpat_heartbeat)

        # setup and run osc server
        self.oscRecv = BlockingOSCUDPServer(("", self.config.get("vrcOscPort")), dispatcher)
        logging.info(f"OSC serving on {self.oscRecv.server_address}")
        self.oscRecv.serve_forever()

    def _MqttReceiverThread(self) -> None:
        def _onMqttConnect(client, userdata, flags, rc) -> None:
            logging.info(f"Connected to mqtt with code {rc}")
            client.subscribe("/dev/patpatpat/in/#")

        def _onMqttMessage(client, userdata, msg) -> None:
            logging.debug(f"{msg.topic} {str(msg.payload)}")
            if msg.topic == "/dev/patpatpat/in/enable":
                # toggle sending of data to the patpatpat hardware
                self.enableVrcTx = bool(int(msg.payload.decode()))
                logging.debug(self.enableVrcTx)

        # setup and connect to mqtt
        self.mqtt = mqtt.Client(client_id="patpatpat-server")
        self.mqtt.on_connect = _onMqttConnect
        self.mqtt.on_message = _onMqttMessage
        self.mqtt.connect(self.config.get("mqttServerIp"), 1883, 60)
        self.mqtt.loop_forever()

    def _mqttPublish(self, addr, data):
        if self.mqtt.is_connected():
            self.mqtt.publish(addr, data)

    def shutdown(self) -> None:
        self.running = False
        self.oscRecv.shutdown()
        self.mqtt.disconnect()