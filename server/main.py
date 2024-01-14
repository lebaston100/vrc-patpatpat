import sys

from PyQt6.QtWidgets import QApplication

from utils import LoggerClass
from modules import config
from ui import MainWindow

logger = LoggerClass.getRootLogger()

REQUIRED_CONFIG_VERSION = 1


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
    logger.info("Starting vrc-patpatpat V0.1")

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
