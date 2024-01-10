"""The main application window
"""

import webbrowser
# from PyQt6.QtCore import pyqtSignal as Signal

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget)

import ui
from modules import config
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setupUi()

        self._logWindow: ui.LogWindow | None = None

    def setupUi(self):
        """Initialize the main UI."""

        # the widget and it's layout
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.sizePolicy().hasHeightForWidth())
        # self.setSizePolicy(sizePolicy) # might not be needed
        self.resize(QSize(800, 430))
        self.setWindowTitle("VRC-patpatpat")
        self.theCentralWidet = QWidget(self)
        self.selfLayout = QVBoxLayout(self.theCentralWidet)
        self.selfLayout.setObjectName("selfLayout")

        # the top bar horizontal layout
        self.hl_topBar = QHBoxLayout()
        self.hl_topBar.setObjectName("hl_topBar")

        # hardware row label
        self.lb_espRowHeader = QLabel(self)
        self.lb_espRowHeader.setObjectName("lb_espRowHeader")
        self.lb_espRowHeader.setText("Hardware:")
        self.hl_topBar.addWidget(self.lb_espRowHeader)

        # help button
        self.bt_openGithub = QPushButton(self)
        self.bt_openGithub.setObjectName("bt_openGithub")
        self.bt_openGithub.setMaximumSize(QSize(60, 16777215))
        self.bt_openGithub.setText("Help")
        self.bt_openGithub.clicked.connect(lambda: webbrowser.open(
            "https://github.com/lebaston100/vrc-patpatpat"))
        self.hl_topBar.addWidget(self.bt_openGithub)

        # open log window button
        self.bt_openLogWindow = QPushButton(self)
        self.bt_openLogWindow.setObjectName("bt_openLogWindow")
        self.bt_openLogWindow.setMaximumSize(QSize(60, 16777215))
        self.bt_openLogWindow.setText("Log")
        self.bt_openLogWindow.clicked.connect(self.handleLogWindowOpen)
        self.hl_topBar.addWidget(self.bt_openLogWindow)

        # open programm settings button
        self.bt_openProgramSettings = QPushButton(self)
        self.bt_openProgramSettings.setObjectName("bt_openProgramSettings")
        self.bt_openProgramSettings.setMaximumSize(QSize(40, 16777215))
        font = QFont()
        font.setPointSize(9)
        self.bt_openProgramSettings.setFont(font)
        self.bt_openProgramSettings.setToolTip("Program Settings")
        self.bt_openProgramSettings.setText("\ud83d\udd27")
        self.hl_topBar.addWidget(self.bt_openProgramSettings)

        self.selfLayout.addLayout(self.hl_topBar)

        # the esp row
        self.espRowFrame = QFrame(self)
        self.espRowFrame.setObjectName("espRowFrame")
        self.espRowFrame.setEnabled(True)
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.espRowFrame.sizePolicy().hasHeightForWidth())
        # self.espRowFrame.setSizePolicy(sizePolicy1)
        self.espRowFrame.setFrameShape(QFrame.Shape.Box)
        self.espRowFrame.setFrameShadow(QFrame.Shadow.Sunken)
        self.espRowFrame.setLineWidth(1)

        # more here

        self.selfLayout.addWidget(self.espRowFrame)

        # contact group label
        self.lb_groupRowHeader = QLabel(self)
        self.lb_groupRowHeader.setObjectName("lb_groupRowHeader")
        self.lb_groupRowHeader.setText("Contact Groups:")
        self.selfLayout.addWidget(self.lb_groupRowHeader)

        # contact group row
        self.groupRowFrame = QFrame(self)
        self.groupRowFrame.setObjectName("groupRowFrame")
        self.groupRowFrame.setFrameShape(QFrame.Shape.Box)
        self.groupRowFrame.setFrameShadow(QFrame.Shadow.Sunken)
        self.groupRowFrame.setLineWidth(1)

        # more here

        self.selfLayout.addWidget(self.groupRowFrame)

        # spacer on bottom of window
        self.pageScalingSpacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.selfLayout.addItem(self.pageScalingSpacer)

        # add layout to central widget to mainwindow
        self.theCentralWidet.setLayout(self.selfLayout)
        self.setCentralWidget(self.theCentralWidet)

    def handleLogWindowOpen(self):
        if self._logWindow:
            self._logWindow.raise_()
            self._logWindow.activateWindow()
        else:
            self._logWindow = ui.LogWindow(logger)
            self._logWindow.destroyed.connect(self.handleLogWindowClose)
            self._logWindow.show()

    def handleLogWindowClose(self):
        if self._logWindow:
            self._logWindow = None

    # handle the close event for the log window
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event (QCloseEvent  |  None]): The qt event.
        """

        logger.debug(f"closeEvent in {__class__.__name__}")

        if self._logWindow:
            self._logWindow.close()


if __name__ == "__main__":
    logger.error("There is no point running this file directly")
