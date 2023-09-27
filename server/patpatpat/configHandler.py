from .jsonFile import FileHelper
from patpatpat import getSubLogger
from pathlib import Path
from typing import Union, Optional, Any

logger = getSubLogger(__name__)


class ConfigHandler:
    """A helper class to handle the config file"""

    def __init__(self, file: str) -> None:
        """Initialize config handler

        Args:
            file (str): A string to the config file

        Raises:
            E: If reading the config file failed
        """
        try:
            self._file = Path(file)
            self._fh = FileHelper(self._file)
        except Exception as E:
            logger.exception(E)
            raise E
        self._configOptions = {}
        self.parse()

    def parse(self) -> None:
        """Read all options from config file.
        If no file exists create an empty one.
        """
        if not self._file.is_file():
            self._flushDataToFile()
        self._configOptions = self._fh.read()

    def get(self, key: str, fallback: Optional[Union[str, None]] = None) -> Any:
        """Return a config option by the given key

        Args:
            key (str): The key to retrieve
            fallback (Optional[Union[str, None]]): The value to return if a config option
            with that name does not exist. Defaults to None.

        Returns:
            Any: _description_
        """
        return self._configOptions.get(key, fallback)

    def has(self, key: str) -> bool:
        """Checks if config contains a given key

        Args:
            key (str): The key to check for

        Returns:
            bool: True if a config option for the key exists, otherwise False
        """
        return bool(key in self._configOptions)

    def set(self, key: str, newVal: Union[str, list, dict, int, float]) -> bool:
        """Set a config option to a new value + trigger flush

        Args:
            key (str): The key to write
            newVal (Union[str, list, dict, int, float]): The value to write for the fiven key

        Returns:
            bool: True if write was successful otherwise False
        """
        self._configOptions[key] = newVal
        logger.debug(f"changed <{key}> to <{newVal}> ({type(key).__name__})")
        return self._flushDataToFile()

    def _flushDataToFile(self) -> bool:
        """Write config options from memory to file

        Returns:
            bool: True if write was successful otherwise False
        """
        return self._fh.write(self._configOptions)


if __name__ == "__main__":
    logger.error("There is no point running this file directly")
