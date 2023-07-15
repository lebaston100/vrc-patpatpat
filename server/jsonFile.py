import json
import logging

class fileHelper:
    """A simple helper class to read and save json from files"""
    def __init__(self, filename) -> None:
        self._filename = filename

    def write(self, data: dict) -> None:
        """dump 'data' to the json file"""
        logging.debug("writing data to json file")
        try:
            with open(self._filename, mode="w") as f:
                f.write(json.dumps(data, indent=4))
        except Exception as E:
            logging.exception(E)
            raise E

    def read(self) -> dict:
        """try to read from json file and return it"""
        logging.debug("reading from json file")
        try:
            with open(self._filename, mode="r") as f:
                data = f.read()
            return json.loads(data)
        except Exception as E:
            logging.exception(E)
            raise E