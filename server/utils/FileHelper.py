import json
from pathlib import Path
from typing import Any

from utils.Logger import LoggerClass
import logging

logger = LoggerClass.getSubLogger(__name__)
logger.setLevel(logger.INFO)  # type: ignore


class FileHelper:
    """A simple helper class to read and save json from files.
    """

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

        # logger.debug("writing data to json file")
        try:
            with open(self._file, mode="w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as E:
            logger.exception(E)
            raise E

    def read(self) -> dict[str, Any]:
        """Read all configration options from file.

        Raises:
            E (Exception): If there was an error while reading the file.

        Returns:
            dict: The data that was read from the file.
        """

        logger.debug("reading from json file")
        try:
            with open(self._file, mode="r") as f:
                return json.load(f)
        except Exception as E:
            logger.exception(E)
            raise E

    def hasData(self) -> bool:
        """Check if the file exists and can be read.

        Returns:
            bool: True if the file exists and can be read,
                False otherwise.
        """

        return self._file.is_file() and bool(self.read())

    def initializeConfig(self) -> None:
        pass


if __name__ == "__main__":
    print("There is no point running this file directly")
