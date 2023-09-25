import logging
from modules.jsonFile import fileHelper


class Config:
    """A helper class to handle the bot config file"""

    def __init__(self, file: str) -> None:
        self._fh = fileHelper(file)
        self._configOptions = None
        self.parse()

    def parse(self) -> None:
        """read config file"""
        self._configOptions = self._fh.read()

    def get(self, key, fallback=None):
        """return a config option by the given key"""
        if self.has(key):
            return self._configOptions[key]
        else:
            return fallback

    def has(self, key):
        return bool(key in self._configOptions)

    def set(self, key, newVal) -> None:
        """set a config option to a new value + trigger flush"""
        self._configOptions[key] = newVal
        self._flushToFile()
        logging.debug(f"changed {key} to {newVal}")

    def _flushToFile(self) -> None:
        """Write config options from memory to file"""
        self._fh.write(self._configOptions)
