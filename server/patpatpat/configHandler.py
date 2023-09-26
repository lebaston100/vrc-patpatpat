from .jsonFile import JsonFileHelper
from patpatpat import getSubLogger
from pathlib import Path

logger = getSubLogger(__name__)


class ConfigHandler:
    """A helper class to handle the config file"""

    def __init__(self, file: str) -> None:
        try:
            self._file = Path(file)
            self._fh = JsonFileHelper(self._file)
        except Exception as E:
            logger.exception(E)
            raise E
        self._configOptions = {}
        self.parse()

    def parse(self) -> None:
        """
        Read all options from config file.
        If no file exists create an empty one.
        """
        if not self._file.is_file():
            self._flushDataToFile()
        self._configOptions = self._fh.read()

    def get(self, key, fallback=None) -> any:
        """return a config option by the given key"""
        if self.has(key):
            return self._configOptions[key]
        else:
            return fallback

    def has(self, key) -> bool:
        """Checks if config contains a given key

        Args:
            key (str): The key to check for

        Returns:
            bool: True if a config option for the key exists, otherwise False
        """
        return bool(key in self._configOptions)

    def set(self, key, newVal) -> None:
        """set a config option to a new value + trigger flush"""
        self._configOptions[key] = newVal
        self._flushDataToFile()
        logger.debug(f"changed <{key}> to <{newVal}> ({type(key).__name__})")

    def _flushDataToFile(self) -> None:
        """Write config options from memory to file"""
        self._fh.write(self._configOptions)


if __name__ == "__main__":
    logger.error("There is no point running this file directly")
