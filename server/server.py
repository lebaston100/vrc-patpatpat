from zeroconf import Zeroconf
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from functools import partial

import threading
import socket
import time
import logging

class Server():
    def __init__(self, window) -> None:
        self.window = window
        self.running = True
        self.reset_values()
        # discover once for now, migrate later without waiting
        self._discover_patstrap()

        # vrchat osc receiver
        threading.Thread(target=self._vrc_osc_recv, args=()).start()

        # the "game loop" aka calculate stuff and send to hardware
        threading.Thread(target=self._update_loop, args=()).start()

    def reset_values(self):
        self.vrc_last_packet = self.patstrap_last_heartbeat = time.time()-5
        self.oscTx = None
        self.numMotors = 2
        self.oscMotorTxData = [255]*self.numMotors

    def _get_patstrap_ip_port(self):
        info = None
        while not info and self.running:
            info = Zeroconf().get_service_info("_osc._udp.local.", "patstrap._osc._udp.local.")
            time.sleep(0.2)
        return (socket.inet_ntoa(info.addresses[0]), info.port)

    def _discover_patstrap(self):
        ip_address, port = self._get_patstrap_ip_port()

        if ip_address is None:
            return False

        logging.debug(f"Patstrap found {ip_address} on port {port}")
        self.oscTx = SimpleUDPClient(ip_address, port)
        return True

    def _update_loop(self, tps=2):

        while self.running:
            if self.oscTx == None:
                break
            
            self.oscTx.send_message("/m", self.oscMotorTxData)

            #intensity = self.window.get_intensity() # this gets the slider setting, ignore for now

            # update gui connection status with a 2 seconds timeout
            self.window.set_vrchat_status(self.vrc_last_packet+1 >= time.time())
            self.window.set_patstrap_status(self.patstrap_last_heartbeat+2 >= time.time())
            time.sleep(1/tps) # replace with something better later
        
        logging.error("Exiting")

    # handle vrchat osc receiving
    def _vrc_osc_recv(self):
        # handle incoming vrchat osc messages
        def _recc_contact(cid, address, val):
            print(f"cid {cid} {address}: {val}")
            self.vrc_last_packet = time.time()
        
        def _recv_patstrap_heartbeat(_, val):
            logging.debug(f"Received patstrap heartbeat with uptime {val/1000}s")
            self.patstrap_last_heartbeat = time.time()

        # register vrchat osc endpoints
        dispatcher = Dispatcher()
        dispatcher.map("/avatar/parameters/pat_neck", partial(_recc_contact, 0))
        dispatcher.map("/avatar/parameters/pat_1", partial(_recc_contact, 1))
        dispatcher.map("/avatar/parameters/pat_2", partial(_recc_contact, 2))
        dispatcher.map("/avatar/parameters/pat_3", partial(_recc_contact, 3))
        dispatcher.map("/patstrap/heartbeat", _recv_patstrap_heartbeat)

        # setup and run osc server
        self.osc = BlockingOSCUDPServer(("", 9001), dispatcher)
        logging.debug(f"OSC serving on {self.osc.server_address}")
        self.osc.serve_forever()

    def shutdown(self):
        self.running = False
        self.osc.shutdown()