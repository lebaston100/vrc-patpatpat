"""Provides an interface to a configuration file in json format.

Typical usage example:

    config = GlobalConfig("myConfig.json")
    config.set("option", "value")
    value = config.get("option")
"""

from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import QMutex, QObject
from PyQt6.QtCore import pyqtSignal as QSignal

from utils import FileHelper, LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class GlobalConfig(QObject):
    """A globaly exposed config object to share program configuration

    Signals:
        configHasChanged(key: str): Emited when a config
            option was updated

    """

    configRootKeyHasChanged = QSignal(str)
    configSubKeyHasChanged = QSignal(str)

    def __init__(self, file: str) -> None:
        """Initialize config handler.

        Args:
            file (str): A path string to the config file.

        Returns:
            None

        Raises:
            E: If reading the config file failed.
        """

        super().__init__()
        logger.debug(f"Creating {__class__.__name__}")

        self.mutex = QMutex()
        try:
            self._file = Path(file)
            self._fh = FileHelper(self._file)
        except Exception as E:
            logger.exception(E)
            raise E
        self._configOptions = {}
        self.parse()

    def parse(self) -> None:
        """
        Reads options from a config file or creates an empty one.

        This function reads all options from a config file. If the file 
        does not exist, it creates an empty one.

        Returns:
            None
        """

        if not self._file.is_file():
            logger.warn("No config file. Creating empty one.")
            self._flushDataToFile()
        self._configOptions = self._fh.read()

    def set(self, key: str,
            newVal: str | list | dict | int | float,
            changedPaths: Optional[list[str]]) -> bool:
        """Set a config option to a new value and trigger a flush.

        Args:
            key (str): The key to write.
            newVal ([str | list | dict | int | float]): The value to
                write for the fiven key.

        Returns:
            bool: True if write was successful otherwise False.
        """

        self.mutex.lock()
        # self._configOptions[key] = newVal
        self._configOptions.update({key: newVal})
        self.mutex.unlock()
        logger.debug(f"changed <{key}> to <{newVal}>")
        self.configRootKeyHasChanged.emit(key)
        if changedPaths:
            for path in changedPaths:
                self.configSubKeyHasChanged.emit(f"{key}.{path}")
        return self._flushDataToFile()

    def get(self, key: str,
            fallback: str | None = None) -> Any:
        """Return a config option by the given key.

        Args:
            key (str): The key to retrieve.
            fallback (Optional[Union[str, None]]): The value to return.
                if a config option with that name does not exist.
                Defaults to None.

        Returns:
            Any: The requested data or the (default) fallback.
        """

        return self._configOptions.get(key, fallback)

    def has(self, key: str) -> bool:
        """Check if config contains a given key.

        Args:
            key (str): The key to check for.

        Returns:
            bool: True if a config option for the key exists,
                otherwise False
        """

        return bool(key in self._configOptions)

    def _flushDataToFile(self) -> bool:
        """Write config options from memory to file.

        Returns:
            bool: True if write was successful otherwise False.
        """

        return self._fh.write(self._configOptions)


# any work to find out what the config would need to be done here
# this is a globally available class INSTANCE, not the class itself
config = GlobalConfig(file="prototype-config.conf")

if __name__ == "__main__":
    print("There is no point running this file directly")
