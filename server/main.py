import sys

from PyQt6.QtWidgets import QApplication

import utils
from ui import MainWindow

logger = utils.LoggerClass.getRootLogger()

if __name__ == "__main__":
    logger.info("Starting vrc-patpatpat V0.1")
    app = QApplication(sys.argv)

    window = MainWindow()
    window.setFixedSize(800, 430)
    window.show()
    sys.exit(app.exec())
