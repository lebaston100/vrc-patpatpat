# type: ignore
# a hacked together utility to record and replay osc data
# help for command line options are available via -h
# timing is not 100% accurate but good enough(TM) for testing purposes
# recorded data is limited to 1 parameter per address

import json
import logging
import threading
import time
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient


class FileHelper:
    """A simple helper class to read and save json from files."""

    def __init__(self, file: str, *args, **kwargs) -> None:
        """Initialize the file helper class.

        Args:
            file (Path): A pathlib.Path object to the config file.
        """
        self._file = Path(file)

    def write(self, data: dict) -> bool:
        """Write all data into the configuration file.

        Args:
            data (dict): The data to write to the file.

        Raises:
            E (Exception): If there was an error writing the file.

        Returns:
            bool: True if the write was sucessful.
        """
        try:
            with open(self._file, mode="w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as E:
            raise E

    def read(self) -> dict[str, Any]:
        """Read all configration options from file.

        Raises:
            E (Exception): If there was an error while reading the file.

        Returns:
            dict: The data that was read from the file.
        """
        try:
            with open(self._file, mode="r") as f:
                return json.load(f)
        except Exception as E:
            raise E

    def hasData(self) -> bool:
        """Check if the file exists and can be read.

        Returns:
            bool: True if the file exists and can be read,
                False otherwise.
        """
        return self._file.is_file() and bool(self.read())


# Import and configure logging
logging.basicConfig(level=logging.DEBUG)

# setup command line argument parser
parser = ArgumentParser(prog="OSCrecreplay",
                        description="Record and replay OSC data")
parser.add_argument(
    "mode", choices=["rec", "play"], help="The mode the script will run in")
parser.add_argument("-i", "--ip", required=False,
                    default="", help="The osc ip to use")
parser.add_argument("-p", "--port", required=False, type=int,
                    default=9001, help="The osc port to use")
parser.add_argument("-n", "--name", required=False, type=str, default="recording.json",
                    help="The filename to use for recording or reading data")
parser.add_argument("-d", "--delay", required=False, type=int, default=0,
                    help="Number of seconds to wait before starting the recording (rec only)")
parser.add_argument("-t", "--timeout", required=False, type=int, default=20,
                    help="Limit runtime to a pecific number of seconds (rec only)")
parser.add_argument("-f", "--filter", required=False, type=str,
                    default="", help="Filter only osc paths containing this string")
args = parser.parse_args()

# init vars
file = FileHelper(args.name)
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
