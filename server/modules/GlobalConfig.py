from PyQt6.QtCore import QObject, QMutex, pyqtSignal as QSignal
from utils import LoggerClass
from utils import ConfigHandler

logger = LoggerClass.getSubLogger(__name__)


class GlobalConfig(QObject):
    """A globaly exposed config object to share program configuration

    Signals:
        configHasChanged(str): Emited when a config option was updated

    """

    configHasChanged = QSignal(str)

    def __init__(self, file: str) -> None:
        """Initialize the config object

        Args:
            file (str): The filename of the config file to use
        """

        super().__init__()
        logger.debug("__init__ GlobalConfig")
        self.mutex = QMutex()
        self.configHandler = ConfigHandler(file)
        logger.debug(self.configHandler._configOptions)

    def set(self, key: str,
            val: [str | list | dict | int | float]) -> None:
        """A set method that uses a mutex to write to the config and
        emits a configHasChanged(key) Signal.

        Args:
            key (str): The root-key to update
            val ([str | list | dict | int | float]): The value 
                to change.
        """

        self.mutex.lock()
        self.configHandler.set(key, val)
        self.mutex.unlock()
        self.configHasChanged.emit(key)


# any work to find out what the config would need to be done here
# this is a globally available class INSTANCE, not the class itself
config = GlobalConfig(file="prototype-config.conf")
