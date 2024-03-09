import logging
import sys

from PyQt6.QtWidgets import QApplication

from modules.GlobalConfig import GlobalConfigSingleton
from utils.Logger import LoggerClass

config = GlobalConfigSingleton.fromFile("config.conf")
logger = LoggerClass.getRootLogger(filename="patpatpat.log")


# set initial logging level for root and child loggers from config
logLevel = config.get("program.logLevel", "INFO")
logger.setLevel(logLevel)
for l in [logging.getLogger(name)
          for name in logging.root.manager.loggerDict]:
    l.setLevel(logLevel)

REQUIRED_CONFIG_VERSION = 1
SEMVER = f"0.1.0"


def handleUncaughtExceptions(exc_type, exc_value, exc_traceback) -> None:
    logger.exception("Unhandled Exception",
                     exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handleUncaughtExceptions


def checkConfigVersion() -> bool:
    """Checks the config version and runs upgrades if needed.
    This can later be moved into it's own module if needed.

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
    from modules.Server import ServerSingleton
    from ui.MainWindow import MainWindow
    logger.info(f"Starting vrc-patpatpat v{SEMVER}")

    # check config version and exit if upgrade did not work
    if not checkConfigVersion():
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("fusion")
    server = ServerSingleton()
    window = MainWindow()
    window.show()

    # Run the app
    returnCode = app.exec()
    logger.info(f"Exiting vrc-patpatpat with return code {returnCode}")
    # Do any other deconstructing here if we need to
    sys.exit(returnCode)
