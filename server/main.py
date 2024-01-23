import logging
import sys

from PyQt6.QtWidgets import QApplication

from modules import config
from ui import MainWindow
from utils import LoggerClass

logger = LoggerClass.getRootLogger()

# set initial logging level for root and child loggers from config
logLevel = config.get("program.logLevel", "INFO")
logger.setLevel(logLevel)
for l in [logging.getLogger(name)
          for name in logging.root.manager.loggerDict]:
    l.setLevel(logLevel)

REQUIRED_CONFIG_VERSION = 1
SEMVER = f"0.1.0"


def handleUncaughtExceptions(exc_type, exc_value, exc_traceback):
    logger.exception("Unhandled Exception",
                     exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handleUncaughtExceptions


def checkConfigVersion() -> bool:
    """Checks the config version and runs upgrades if needed.

    Returns:
        bool: True if config (and upgrade) was ok, False otherwise
    """

    logger.debug("Checking config version")
    configVersion = config.get("configVersion", 0)
    if configVersion < REQUIRED_CONFIG_VERSION:
        logger.info("Config needs upgrade")
    else:
        logger.info("Config version is ok")
    return True


if __name__ == "__main__":
    logger.info(f"Starting vrc-patpatpat v{SEMVER}")

    # check config version and exit if upgrade did not work
    if not checkConfigVersion():
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    returnCode = app.exec()
    logger.info(f"Exiting vrc-patpatpat with return code {returnCode}")
    # Do any other deconstructing here if we need to
    sys.exit(returnCode)
