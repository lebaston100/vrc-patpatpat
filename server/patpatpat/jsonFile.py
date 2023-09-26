import json
from patpatpat import getSubLogger
from pathlib import Path

logger = getSubLogger(__name__)


class JsonFileHelper:
    """A simple helper class to read and save json from files"""

    def __init__(self, file: Path) -> None:
        self._file = file

    def write(self, data: dict) -> None:
        """dump 'data' to the json file"""
        logger.debug("writing data to json file")
        try:
            with open(self._file, mode="w") as f:
                f.write(json.dumps(data, indent=4))
        except Exception as E:
            logger.exception(E)
            raise E

    def read(self) -> dict:
        """try to read from json file and return it"""
        logger.debug("reading from json file")
        try:
            with open(self._file, mode="r") as f:
                data = f.read()
            return json.loads(data)
        except Exception as E:
            logger.exception(E)
            raise E


if __name__ == "__main__":
    logger.error("There is no point running this file directly")
