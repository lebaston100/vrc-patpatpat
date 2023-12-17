"""The main application window
"""

# from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QPushButton

import ui
from modules import config
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.testButton = QPushButton()
        self.testButton.setText("open")

        self.setCentralWidget(self.testButton)
        self.testButton.clicked.connect(self.showTestWindow)

        config.configRootKeyHasChanged.connect(self.configChanged)
        config.configSubKeyHasChanged.connect(self.configChanged)

        self.setupUi()

    def configChanged(self, key):
        logger.debug(f"config changed for key '{key}'")

    def showTestWindow(self):
        self.testWindow = ui.EspSettingsDialog()
        self.testWindow.show()
        self.testWindow.destroyed.connect(
            self.programSettingsWindowClosed)

    def programSettingsWindowClosed(self):
        self.testWindow = None

    # handle the close event for the log window
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event (QCloseEvent  |  None]): The qt event.
        """

        logger.debug(f"closeEvent in {__class__.__name__}")

        # close program config window if open
        # if hasattr(self, "programSettingsDialog"):
        # self.programSettingsDialog.close()

    def setupUi(self):
        pass


if __name__ == "__main__":
    logger.error("There is no point running this file directly")
