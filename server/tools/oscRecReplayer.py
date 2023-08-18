# a hacked together utility to record and replay osc data
# help for command line options are available via -h
# timing is not 100% accurate but good enough(TM) for testing purposes
# recorded data is limited to 1 parameter per address

from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from argparse import ArgumentParser
import sys
import pathlib
sys.path.append(pathlib.Path("../").resolve().as_posix())
from modules.jsonFile import fileHelper
import threading
import time

# Import and configure logging
import logging
logging.basicConfig(level=logging.DEBUG)

# setup command line argument parser
parser = ArgumentParser(prog="OSCrecreplay", description="Record and replay OSC data")
parser.add_argument("mode", choices=["rec", "play"], help="The mode the script will run in")
parser.add_argument("-i", "--ip", required=False, default="" ,help="The osc ip to use")
parser.add_argument("-p", "--port", required=False, type=int, default=9001, help="The osc port to use")
parser.add_argument("-n", "--name", required=False, type=str, default="recording.json", help="The filename to use for recording or reading data")
parser.add_argument("-d", "--delay", required=False, type=int, default=0, help="Number of seconds to wait before starting the recording (rec only)")
parser.add_argument("-t", "--timeout", required=False, type=int, default=20, help="Limit runtime to a pecific number of seconds (rec only)")
parser.add_argument("-f", "--filter", required=False, type=str, default="", help="Filter only osc paths containing this string")
args = parser.parse_args()

# init vars
file = fileHelper(args.name)
dataBuffer = []
startTime = 0

def osc_recv_handler(address, *argss):
    global startTime
    if not args.filter or (args.filter and args.filter in address):
        logging.debug(f"OSC IN {address}: {argss}")
        dataBuffer.append([time.time()-startTime, address, argss[0]])

def recorderLoop(server):
    server.serve_forever()
    server.close()
    
def runRecorder():
    global startTime
    dispatcher = Dispatcher()
    dispatcher.set_default_handler(osc_recv_handler)
    server = BlockingOSCUDPServer((args.ip, args.port), dispatcher)

    thread = threading.Thread(target=recorderLoop, args=(server,))
    thread.daemon = True
    startTime = time.time()
    thread.start()
    logging.debug("Server started")

    try:
        time.sleep(args.timeout)
    except KeyboardInterrupt:
        logging.debug("Starting shutdown")
    finally:
        server.shutdown()
        logging.info("Dumping data")
        logging.debug(dataBuffer)
        file.write(dataBuffer)
        logging.info("Exiting...")

def runReplayer():
    oscClient = SimpleUDPClient(args.ip, args.port)
    data = file.read()
    # validate that we have in fact data
    if len(data) < 1:
        return None
    logging.debug(data)
    t1 = time.time()
    for m in data:
        t, addr, d = m
        time.sleep(max(t1-time.time()+t, 0))
        oscClient.send_message(addr, d)
    logging.info("Exiting...")

def main():
    time.sleep(args.delay)
    if args.mode == "rec":
        runRecorder()
    elif args.mode == "play":
        runReplayer()

if __name__ == "__main__":
    main()