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
        self.reset_values()
        # run hardware discovery in seperate thread to not wait for it
        threading.Thread(target=self._discover_patstrap, args=()).start()

        # vrchat and patstrap osc receiver
        threading.Thread(target=self._osc_recv, args=()).start()

        # the "game loop" aka calculate stuff and send to hardware
        threading.Thread(target=self._main_loop, args=()).start()

        # mqtt control interface (might expand or remove in the future)
        threading.Thread(target=self._run_mqtt, args=()).start()

    def reset_values(self) -> None:
        """Initialize some internal values"""
        self.vrc_last_packet = self.patstrap_last_heartbeat = time.time()-5
        self.enableVrcTx = True
        self.battery = 0
        self.numMotors = self.config.get("numMotors", 2)
        self.oscMotorTxData = [0]*self.numMotors
        self.vrcInValues = {}
        self.patstrapIsConnected = False
        for i in range(4):
            self.vrcInValues[i] = {"v": 0, "ts": 0}
        self.avatarPoints = [self.config.get(f"avatarPoint{avatarPointId}") for avatarPointId in range(4)]
        self.avatarPointsAsTuple = [(p["x"], p["y"], p["z"]) for p in self.avatarPoints]
        # Show avatar points in visualizer
        self.window.qt3dplot.addSeries(self._generateAvatarPointSeries([QScatterDataItem(QVector3D(*p)) for p in self.avatarPointsAsTuple]))
        self._generateCalculatedPointSeries()

    def _generateAvatarPointSeries(self, data) -> QScatter3DSeries:
        """A scatter serie to display the contact receiver positions"""
        proxy = QScatterDataProxy()
        proxy.addItems(data)
        series = QScatter3DSeries()
        series.setItemSize(0.2)
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
        self.window.qt3dplot.addSeries(resultSeries)

    def _get_patstrap_ip_port(self) -> tuple[str, int]:
        info = None
        self.zc = Zeroconf()
        while not info and self.running:
            info = self.zc.get_service_info("_osc._udp.local.", "patstrap._osc._udp.local.", timeout=1500)
            time.sleep(0.1)
        if info:
            return (socket.inet_ntoa(info.addresses[0]), info.port)
        return (None, None)

    def _discover_patstrap(self) -> bool:
        ip_address, port = self._get_patstrap_ip_port()

        if ip_address is None or port is None:
            return

        logging.info(f"Patstrap found {ip_address} on port {port}")
        self.oscTx = SimpleUDPClient(ip_address, port)

    def _validate_data_age(self, d: dict) -> bool:
        """Check that all received points are fresh"""
        maxAge = time.time()-0.2
        return all(e["ts"] > maxAge for e in d.values())

    def _process_3d_position(self, d: dict) -> tuple:
        """Calculate the 3d point"""
        if self._validate_data_age(d):
            # run a mlat solver over the anchor points and the reported distances
            solver = Engine()
            for id, point in enumerate(self.avatarPointsAsTuple):
                solver.add_anchor(f"anchor_{id}", point)
                solver.add_measure_id(f"anchor_{id}", d[id]["v"])
            result = solver.solve()
            if result:
                return result
        return None
    
    def _mplatPointToQ3DScatterItem(self, point: mlatPoint):
        """Convert the 3D Resolver point to a QT Point"""
        return QScatterDataItem(QVector3D(point.x, point.y, point.z))
    
    # we need a server and gui function to update the 3d visualizer

    def _main_loop(self, tps: int=60) -> None:
        
        # add some static points just for axis scaling
        self.window.qt3dplot.seriesList()[0].dataProxy().addItems([QScatterDataItem(QVector3D(-0.5,-0.5,-0.5)),QScatterDataItem(QVector3D(0.5,0.5,0.5))])

        while self.running:
            loopStart = time.perf_counter_ns()
            if self.oscTx == None:
                continue
            
            # calculate the 3d position from the input data
            pos = self._process_3d_position(self.vrcInValues)
            if pos:
                # we got a position from our calculations back
                logging.debug(pos)
                # add to visualizer
                # TODO: Cleanup
                if len(self.window.qt3dplot.seriesList()[1].dataProxy().array()) > 150:
                    self.window.qt3dplot.seriesList()[1].dataProxy().removeItems(0, 1) # create trail
                self.window.qt3dplot.seriesList()[1].dataProxy().addItem(self._mplatPointToQ3DScatterItem(pos))

            # project 3d point onto motor sphere
            # TODO

            #intensity = self.window.get_intensity() # this gets the slider setting, ignore for now

            if self.enableVrcTx:
                # Only send data here
                # send out motor speeds
                self.oscTx.send_message("/m", self.oscMotorTxData)
                pass

            # update gui connection status with a 2 seconds timeout
            # once i learn qt signals maybe this can be event based?
            self.window.set_vrchat_status(self.vrc_last_packet+1 >= time.time())
            self.patstrapIsConnected = self.patstrap_last_heartbeat+2 >= time.time()
            self.window.set_patstrap_status(self.patstrapIsConnected)

            # calculate loop time
            loopEnd = time.perf_counter_ns()
            logging.debug(f"loop time: {(loopEnd-loopStart)/1000000}ms")
            #self._mqtt_send("dev/patstrap/out/loopperf", (loopEnd-loopStart)/1000000)
            time.sleep(max((1/tps)-(loopEnd-loopStart)/1000000000, 0))
        
        logging.info("Exiting...")

    # handle vrchat osc receiving
    def _osc_recv(self) -> None:
        # handle incoming vrchat osc messages
        def _recv_contact(address, cid, val) -> None:
            #logging.debug(f"cid {cid[0]} {address}: {val}")
            # invert value and scale it according to the colliders size
            scaledval = (1.0-val)*self.avatarPoints[cid[0]]["r"]
            self.vrcInValues[cid[0]] = {"v": scaledval, "ts": time.time()}
            self.vrc_last_packet = time.time()
        
        def _recv_patstrap_heartbeat(_, uptime, voltage) -> None:
            #logging.debug(f"Received patstrap heartbeat with uptime {uptime}s and voltage {voltage}")
            self._mqtt_send("dev/patstrap/out/heartbeat", uptime)
            self.patstrap_last_heartbeat = time.time()

            # for now this is just the raw value, we later need to do some light processing to it
            self.battery = int(voltage)
            self.window.set_patstrap_battery(self.battery)
            
        # register vrchat osc endpoints
        dispatcher = Dispatcher()
        dispatcher.map("/avatar/parameters/pat_center", _recv_contact, 0)
        dispatcher.map("/avatar/parameters/pat_1", _recv_contact, 1)
        dispatcher.map("/avatar/parameters/pat_2", _recv_contact, 2)
        dispatcher.map("/avatar/parameters/pat_3", _recv_contact, 3)
        dispatcher.map("/patstrap/heartbeat", _recv_patstrap_heartbeat)

        # setup and run osc server
        self.osc = BlockingOSCUDPServer(("", self.config.get("vrcOscPort")), dispatcher)
        logging.info(f"OSC serving on {self.osc.server_address}")
        self.osc.serve_forever()

    def _run_mqtt(self) -> None:
        def _on_connect(client, userdata, flags, rc) -> None:
            logging.info(f"Connected to mqtt with code {rc}")
            client.subscribe("/dev/patstrap/in/#")

        def _on_message(client, userdata, msg) -> None:
            logging.debug(f"{msg.topic} {str(msg.payload)}")
            if msg.topic == "/dev/patstrap/in/enable":
                # toggle sending of data to the patstrap hardware
                self.enableVrcTx = bool(int(msg.payload.decode()))
                logging.debug(self.enableVrcTx)

        # setup and connect to mqtt
        self.mqtt = mqtt.Client(client_id="patstrap-server")
        self.mqtt.on_connect = _on_connect
        self.mqtt.on_message = _on_message
        self.mqtt.connect(self.config.get("mqttServerIp"), 1883, 60)
        self.mqtt.loop_forever()

    def _mqtt_send(self, addr, data):
        if self.mqtt.is_connected():
            self.mqtt.publish(addr, data)

    def shutdown(self) -> None:
        self.running = False
        self.osc.shutdown()
        self.mqtt.disconnect()