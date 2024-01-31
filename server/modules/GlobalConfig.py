"""Provides an interface to a configuration file in json format.

Typical usage example:

    config = GlobalConfig("myConfig.json")
    config.set("option", "value")
    value = config.get("option")
"""

import re
from typing import Any, Callable, Optional, Type, TypeVar

from PyQt6.QtCore import QMutex, QObject
from PyQt6.QtCore import pyqtSignal as QSignal

from utils import FileHelper, LoggerClass, PathReader

logger = LoggerClass.getSubLogger(__name__)

T = TypeVar('T', bound='GlobalConfigSingleton')


class GlobalConfigSingleton(QObject):
    """
    Singleton class for global configuration.

    Attributes:
        __instance (GlobalConfigSingleton): Singleton instance.
        configPathHasChanged (QSignal): Signal for config path change.
        configPathWasDeleted (QSignal): Signal for config path deletion.
    """

    __instance = None
    configPathHasChanged = QSignal(str)
    configRootUpdateDone = QSignal(str)
    configPathWasDeleted = QSignal(str)

    @classmethod
    def getInstance(cls: Type[T]) -> Optional[T]:
        """
        Get the singleton instance.

        Returns:
            GlobalConfigSingleton: Singleton instance.
        """

        return cls.__instance

    @classmethod
    def fromFile(cls: Type[T], filename: str) -> T:
        return cls(FileHelper(filename))

    def __init__(self, configHandler: FileHelper, *args, **kwargs) -> None:
        """
        Initialize the singleton instance.

        Args:
            configHandler (FileHelper): Config file handler.

        Raises:
            RuntimeError: If multiple singleton instances are initialized.
        """

        if GlobalConfigSingleton.__instance:
            raise RuntimeError("Can't initialize multiple singleton instances")

        super().__init__()
        logger.debug(f"Creating {__class__.__name__}")

        self._mutex = QMutex()
        self._configHandler = configHandler
        self._configOptions: dict[str, Any] = {}
        self._configPathChangedCallbacks: dict[str, Callable] = {}
        self._configPathDeletedCallbacks: dict[str, Callable] = {}

        try:
            self.parse()
        except Exception as E:
            logger.exception(E)
            raise E

        self.configPathHasChanged.connect(self._runChangeCallbacks)
        self.configPathWasDeleted.connect(self._runRemoveCallbacks)
        GlobalConfigSingleton.__instance = self

    def parse(self) -> None:
        """
        Parse the config file.

        Raises:
            RuntimeError: If config file is not found.
        """

        if not self._configHandler.hasData():
            logger.warn("No config file. Creating empty one.")
            self._configHandler.initializeConfig()
            self._writeOptions()
        self._configOptions = self._configHandler.read()

    def set(self, path: str,
            newVal: str | list | dict | int | float,
            wasChanged: bool = False) -> bool:
        """Set a config option to a new value and trigger a flush.

        Args:
            path (str): The key to write.
            newVal ([str | list | dict | int | float]): The value to
                write for the fiven key.
            wasChanged (bool): If the path was changed and a signal
                should be emitted

        Returns:
            bool: True if flush was successful otherwise False.
        """

        try:
            self._mutex.lock()
            self._configOptions.update(PathReader.setOption(
                self._configOptions, path, newVal))
            # logger.debug(f"changed <{path}> to <{newVal}>")
        except Exception as E:
            logger.exception(E)
            return False
        else:
            if wasChanged:
                self.configPathHasChanged.emit(path)
            return self._writeOptions()
        finally:
            self._mutex.unlock()

    def get(self, path: str,
            fallback: Any = None) -> Any:
        """Return a config option by the given key.

        Args:
            path (str): The path to traverse.
            fallback (Optional[Union[str, None]]): The value to return.
                if a config option with that name does not exist.
                Defaults to None.

        Returns:
            Any: The requested data or the (default) fallback.
        """

        try:
            option = PathReader.getOption(self._configOptions, path)
        except:
            return fallback
        else:
            return option

    def has(self, path: str) -> bool:
        """Check if config contains a given key.

        Args:
            path (str): The key to check for.

        Returns:
            bool: True if a config option for the key exists,
                otherwise False
        """

        try:
            PathReader.getOption(self._configOptions, path)
        except:
            return False
        else:
            return True

    def delete(self, path: str) -> None:
        """Deletes something from inside a (nested) dict.

        This is an in-place operation just like del a["b"]!

        Args:
            path (str): The path to the option to delete written in
                dot notation.

        Returns:
            None
        """

        PathReader.delOption(self._configOptions, path)
        self.configPathWasDeleted.emit(path)

    def _writeOptions(self) -> bool:
        """Write config options from memory to file.

        Returns:
            bool: True if write was successful otherwise False.
        """

        return self._configHandler.write(self._configOptions)

    def registerChangeCallback(self, pathPattern: str, callback: Callable) -> None:
        """
        Register a callback for a configuration change.

        Args:
            pathPattern (str): Regex pattern of the path to watch for changes.
            callback (Callable): Function to call when a change is detected.
        """

        self._configPathChangedCallbacks.update({pathPattern: callback})
        logger.debug(self._configPathChangedCallbacks)

    def deleteChangeCallback(self, pathPattern: str) -> None:
        """
        Remove a registered callback.

        Args:
            pathPattern (str): Regex pattern of the path of the callback
                to remove.
        """

        try:
            self._configPathChangedCallbacks.pop(pathPattern)
        except:
            logger.error(f"Path {pathPattern} has no registered callbacks")
        logger.debug(self._configPathChangedCallbacks)

    def _runChangeCallbacks(self, changedPath: str) -> None:
        """
        Run callbacks for a given changed path.

        Args:
            changedPath (str): The path that has changed.
        """

        for pathPattern, cb in self._configPathChangedCallbacks.items():
            if re.match(pathPattern + "$", changedPath):
                cb(changedPath)

    def registerRemoveCallback(self, pathPattern: str, callback: Callable) -> None:
        """
        Register a callback for a configuration change.

        Args:
            pathPattern (str): Regex pattern of the path to watch for changes.
            callback (Callable): Function to call when a change is detected.
        """

        self._configPathDeletedCallbacks.update({pathPattern: callback})
        logger.debug(self._configPathDeletedCallbacks)

    def deleteRemoveCallback(self, pathPattern: str) -> None:
        """
        Remove a registered callback.

        Args:
            pathPattern (str): Regex pattern of the path of the callback
                to remove.
        """

        try:
            self._configPathDeletedCallbacks.pop(pathPattern)
        except:
            logger.error(f"Path {pathPattern} has no registered callbacks")
        logger.debug(self._configPathDeletedCallbacks)

    def _runRemoveCallbacks(self, removedPath: str) -> None:
        """
        Run callbacks for a given removed path.

        Args:
            removedPath (str): The path that has changed.
        """

        for pathPattern, cb in self._configPathDeletedCallbacks.items():
            if re.match(pathPattern + "$", removedPath):
                cb(removedPath)


# any work to find out what the config would need to be done here
# this is a globally available class INSTANCE, not the class itself
config = GlobalConfigSingleton.fromFile("prototype-config.conf")

if __name__ == "__main__":
    print("There is no point running this file directly")
