import sys

from PyQt6.QtWidgets import QApplication

import utils
from modules import config
from ui import MainWindow

logger = utils.LoggerClass.getRootLogger()

REQUIRED_CONFIG_VERSION = 1


def checkConfigVersion() -> bool:
    logger.debug("Checking config version")
    configVersion = config.get("configVersion", 0)
    if configVersion < REQUIRED_CONFIG_VERSION:
        logger.info("Config needs upgrade")
    else:
        logger.info("Config version is ok")
    return True


if __name__ == "__main__":
    logger.info("Starting vrc-patpatpat V0.1")
    checkConfigVersion()
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
