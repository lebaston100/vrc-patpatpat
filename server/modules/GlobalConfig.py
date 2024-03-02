"""Provides an interface to a configuration file in json format.

Typical usage example:

    config = GlobalConfig("myConfig.json")
    config.set("option", "value")
    value = config.get("option")
"""

import re
from typing import Any, Optional, TypeVar

from PyQt6.QtCore import QMutex, QObject
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtBoundSignal
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
    def getInstance(cls: type[T]) -> Optional[T]:
        """Get the singleton instance.

        Returns:
            GlobalConfigSingleton: Singleton instance.
        """
        return cls.__instance

    @classmethod
    def fromFile(cls: type[T], filename: str) -> T:
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
        self._configHandler.createBackup()
        self._configOptions: dict[str, Any] = {}
        self._configPathChangedSignals: dict[str, list[pyqtBoundSignal]] = {}
        self._configPathDeletedSignals: dict[str, list[pyqtBoundSignal]] = {}

        try:
            self.parse()
        except Exception as E:
            logger.exception(E)
            raise E

        self.configPathHasChanged.connect(self._runChangeSignals)
        self.configPathWasDeleted.connect(self._runRemoveSignals)
        GlobalConfigSingleton.__instance = self

    def parse(self) -> None:
        """Parse the config file.

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
                write for the given key.
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

    def delete(self, path: str) -> bool:
        """Deletes something from inside a (nested) dict.

        This is an in-place operation just like del a["b"]!

        Args:
            path (str): The path to the option to delete written in
                dot notation.

        Returns:
            None
        """
        try:
            self._mutex.lock()
            PathReader.delOption(self._configOptions, path)
        except Exception as E:
            logger.exception(E)
            return False
        else:
            self.configPathWasDeleted.emit(path)
            return self._writeOptions()
        finally:
            self._mutex.unlock()

    def _writeOptions(self) -> bool:
        """Write config options from memory to file.

        Returns:
            bool: True if write was successful otherwise False.
        """
        return self._configHandler.write(self._configOptions)

    def _registerSignalForSignals(self, signalList: dict, pathPattern: str,
                                  signal: pyqtBoundSignal) -> None:
        """A helper function to avoid code duplication"""
        if not pathPattern in signalList:
            signalList.update({pathPattern: []})
        if not signal in signalList[pathPattern]:
            signalList[pathPattern].append(signal)
        # logger.debug(f"Signals after register: {str(signalList)}")

    def _removeSignalForSignals(self, signalList: dict,
                                signal: pyqtBoundSignal) -> None:
        """A helper function to avoid code duplication"""
        try:
            keys_to_remove = []
            for key, signals in signalList.items():
                if signal in signals:
                    signals.remove(signal)
                    if not signals:
                        keys_to_remove.append(key)
            for key in keys_to_remove:
                del signalList[key]
        except:
            pass
        # logger.debug(f"Remaining signals after delete: {str(signalList)}")

    def _emitSignalsForPath(self, signalList: dict,
                            changedPath: str) -> None:
        """A helper function to avoid code duplication"""
        # logger.debug(f"Signals before emit of "
        #  f"{changedPath}: {str(signalList)}")
        for pathPattern, signals in signalList.items():
            if re.match(pathPattern + "$", changedPath):
                logger.debug(f"Matching signals for {pathPattern}:"
                             f"{str(signals)}")
                for signal in signals:
                    signal.emit(changedPath)

    def registerChangeSignal(self, pathPattern: str,
                             signal: pyqtBoundSignal) -> None:
        """Register a signal to be emitted for a configuration change.

        Args:
            pathPattern (str): Regex pattern of the path to watch for changes.
            signal (pyqtBoundSignal): Signal to emit when a change is detected.
        """
        self._registerSignalForSignals(
            self._configPathChangedSignals, pathPattern, signal)

    def deleteChangeSignal(self, signal: pyqtBoundSignal) -> None:
        """Remove a registered signal for all pathPatterns.

        Args:
            signal (pyqtBoundSignal): The signal to remove.
        """
        self._removeSignalForSignals(self._configPathChangedSignals, signal)

    def _runChangeSignals(self, changedPath: str) -> None:
        """Emit signals for a given changed path.

        Args:
            changedPath (str): The path that has changed.
        """
        self._emitSignalsForPath(self._configPathChangedSignals, changedPath)

    def registerRemoveSignal(self, pathPattern: str,
                             signal: pyqtBoundSignal) -> None:
        """Register a signal to be emitted for a configuration change.

        Args:
            pathPattern (str): Regex pattern of the path to watch for changes.
            signal (pyqtBoundSignal): Signal to emit when a change is detected.
        """
        self._registerSignalForSignals(
            self._configPathDeletedSignals, pathPattern, signal)

    def deleteRemoveSignal(self, signal: pyqtBoundSignal) -> None:
        """Remove a registered signal.

        Args:
            pathPattern (str): Regex pattern of the path of the signal
                to remove.
        """
        self._removeSignalForSignals(self._configPathDeletedSignals, signal)

    def _runRemoveSignals(self, removedPath: str) -> None:
        """Emit signals for a given removed path.

        Args:
            removedPath (str): The path that has changed.
        """
        self._emitSignalsForPath(self._configPathDeletedSignals, removedPath)


# any work to find out what the config would need to be done here
# this is a globally available class INSTANCE, not the class itself
config = GlobalConfigSingleton.fromFile("config.conf")

if __name__ == "__main__":
    print("There is no point running this file directly")
