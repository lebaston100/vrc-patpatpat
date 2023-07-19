from zeroconf import Zeroconf
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from functools import partial
import paho.mqtt.client as mqtt

# for docstrings
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
        # discover once for now, migrate later without waiting
        self._discover_patstrap()

        # vrchat and patstrap osc receiver
        threading.Thread(target=self._osc_recv, args=()).start()

        # the "game loop" aka calculate stuff and send to hardware
        threading.Thread(target=self._update_loop, args=()).start()

        # leb0-specific mqtt control interface
        threading.Thread(target=self._run_mqtt, args=()).start()

    def reset_values(self) -> None:
        self.vrc_last_packet = self.patstrap_last_heartbeat = time.time()-5
        self.enableVrcTx = False
        self.numMotors = self.config.get("numMotors", 2)
        self.oscMotorTxData = [0]*self.numMotors
        self.vrcInValues = {}
        for i in range(4):
            self.vrcInValues[i] = {"v": 0, "ts": 0}

    def _get_patstrap_ip_port(self) -> tuple[str, int]:
        info = None
        self.zc = Zeroconf()
        while not info and self.running:
            info = self.zc.get_service_info("_osc._udp.local.", "patstrap._osc._udp.local.")
            time.sleep(0.2)
        return (socket.inet_ntoa(info.addresses[0]), info.port)

    def _discover_patstrap(self) -> bool:
        ip_address, port = self._get_patstrap_ip_port()

        if ip_address is None or port is None:
            return False

        logging.debug(f"Patstrap found {ip_address} on port {port}")
        self.oscTx = SimpleUDPClient(ip_address, port)
        return True

    def _update_loop(self, tps=2) -> None:
        while self.running:
            loopStart = time.perf_counter_ns()
            if self.oscTx == None:
                break
            
            self.oscTx.send_message("/m", self.oscMotorTxData)

            #intensity = self.window.get_intensity() # this gets the slider setting, ignore for now

            if self.enableVrcTx:
                # Only send data here
                pass

            # update gui connection status with a 2 seconds timeout
            self.window.set_vrchat_status(self.vrc_last_packet+1 >= time.time())
            self.window.set_patstrap_status(self.patstrap_last_heartbeat+2 >= time.time())
            logging.debug(self.vrcInValues)

            # calculate loop time
            loopEnd = time.perf_counter_ns()
            #logging.debug(f"current main loop time: {(loopEnd-loopStart)/1000000}ms")
            #self._mqtt_send("dev/patstrap/out/loopperf", (loopEnd-loopStart)/1000000)
            time.sleep((1/tps)-(loopEnd-loopStart)/1000000000)
        
        logging.error("Exiting...")

    # handle vrchat osc receiving
    def _osc_recv(self) -> None:
        # handle incoming vrchat osc messages
        def _recv_contact(cid, address, val) -> None:
            #logging.debug(f"cid {cid} {address}: {val}")
            self.vrcInValues[cid] = {"v": val, "ts": time.time()}
            self.vrc_last_packet = time.time()
        
        def _recv_patstrap_heartbeat(_, val) -> None:
            #logging.debug(f"Received patstrap heartbeat with uptime {val}s")
            self._mqtt_send("dev/patstrap/out/heartbeat", val)
            self.patstrap_last_heartbeat = time.time()

        # register vrchat osc endpoints
        dispatcher = Dispatcher()
        dispatcher.map("/avatar/parameters/pat_neck", partial(_recv_contact, 0))
        dispatcher.map("/avatar/parameters/pat_1", partial(_recv_contact, 1))
        dispatcher.map("/avatar/parameters/pat_2", partial(_recv_contact, 2))
        dispatcher.map("/avatar/parameters/pat_3", partial(_recv_contact, 3))
        dispatcher.map("/patstrap/heartbeat", _recv_patstrap_heartbeat)

        # setup and run osc server
        self.osc = BlockingOSCUDPServer(("", self.config.get("vrcOscPort")), dispatcher)
        logging.debug(f"OSC serving on {self.osc.server_address}")
        self.osc.serve_forever()

    def _run_mqtt(self) -> None:
        def _on_connect(client, userdata, flags, rc) -> None:
            logging.debug(f"Connected to mqtt with code {rc}")
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