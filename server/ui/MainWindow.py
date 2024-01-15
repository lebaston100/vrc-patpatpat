"""The main application window
"""

import webbrowser
from functools import partial

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QScrollArea, QSizePolicy,
                             QSpacerItem, QVBoxLayout, QWidget)

import ui
from modules import config
from utils import LoggerClass

# from PyQt6.QtCore import pyqtSignal as Signal


logger = LoggerClass.getSubLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._singleWindows: dict[str, QWidget] = {}

        self.setupUi()

    def setupUi(self) -> None:
        """Initialize the main UI."""

        # the widget and it's layout
        self.setWindowTitle("VRC-patpatpat")
        self.resize(QSize(800, 430))
        self.setMaximumWidth(2000)
        self.setMinimumWidth(600)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.setSizePolicy(sizePolicy)
        self.theCentralWidet = QWidget(self)
        self.selfLayout = QVBoxLayout(self.theCentralWidet)

        # the top bar horizontal layout
        self.hl_topBar = QHBoxLayout()

        # hardware row label
        self.lb_espRowHeader = QLabel(self)
        self.lb_espRowHeader.setText("Hardware:")
        self.hl_topBar.addWidget(self.lb_espRowHeader)

        # help button
        self.bt_openGithub = QPushButton(self)
        self.bt_openGithub.setMaximumWidth(60)
        self.bt_openGithub.setText("Help")
        self.bt_openGithub.clicked.connect(lambda: webbrowser.open(
            "https://github.com/lebaston100/vrc-patpatpat"
            "?tab=readme-ov-file#vrc-patpatpat"))
        self.hl_topBar.addWidget(self.bt_openGithub)

        # open log window button
        self.bt_openLogWindow = QPushButton(self)
        self.bt_openLogWindow.setMaximumWidth(60)
        self.bt_openLogWindow.setText("Log")
        self.bt_openLogWindow.clicked.connect(
            partial(self.openSingleWindow, "LogWindow"))
        self.hl_topBar.addWidget(self.bt_openLogWindow)

        # open programm settings button
        self.bt_openProgramSettings = QPushButton(self)
        self.bt_openProgramSettings.setMaximumWidth(40)
        font = QFont()
        font.setPointSize(9)
        self.bt_openProgramSettings.setFont(font)
        self.bt_openProgramSettings.setToolTip("Program Settings")
        self.bt_openProgramSettings.setText("\ud83d\udd27")
        self.bt_openProgramSettings.clicked.connect(
            partial(self.openSingleWindow, "ProgramSettingsDialog"))
        self.hl_topBar.addWidget(self.bt_openProgramSettings)

        self.selfLayout.addLayout(self.hl_topBar)

        # the esp row

        # the hardware scroll area
        self.hardwareScrollArea = self.createScrollArea()

        # the single widget inside the scroll area
        self.hardwareScrollAreaWidgetContent = QWidget(self.hardwareScrollArea)
        self.hardwareScrollAreaWidgetContent.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum))

        # the layout inside the widget that's inside the scroll area
        self.hardwareScrollAreaWidgetContentLayout = QVBoxLayout(
            self.hardwareScrollAreaWidgetContent)
        self.hardwareScrollAreaWidgetContentLayout.setContentsMargins(
            0, 0, 0, 0)

        # a test entry in the hardware row
        self.testHwInstance1 = HardwareEspRow(
            self.hardwareScrollAreaWidgetContent)
        self.testHwInstance2 = HardwareEspRow(
            self.hardwareScrollAreaWidgetContent)
        self.testHwInstance3 = HardwareEspRow(
            self.hardwareScrollAreaWidgetContent)
        self.testHwInstance4 = HardwareEspRow(
            self.hardwareScrollAreaWidgetContent)

        # add a few test entries to the scrollAreasWidgets layout
        # this will later be done programatically
        self.hardwareScrollAreaWidgetContentLayout.addWidget(
            self.testHwInstance1)
        self.hardwareScrollAreaWidgetContentLayout.addWidget(
            self.testHwInstance2)
        self.hardwareScrollAreaWidgetContentLayout.addWidget(
            self.testHwInstance3)
        self.hardwareScrollAreaWidgetContentLayout.addWidget(
            self.testHwInstance4)

        # set the hardware scroll areas only widget to our scrollarea content widget
        self.hardwareScrollArea.setWidget(self.hardwareScrollAreaWidgetContent)
        # finally add the scroll area to out main window layout
        self.selfLayout.addWidget(self.hardwareScrollArea)

        # contact group label
        self.lb_groupRowHeader = QLabel(self)
        self.lb_groupRowHeader.setText("Contact Groups:")
        self.selfLayout.addWidget(self.lb_groupRowHeader)

        # contact group row
        self.groupRowFrame = QFrame(self)
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

    def createScrollArea(self) -> QScrollArea:
        scrollArea = QScrollArea(self)
        scrollArea.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        scrollArea.setMinimumSize(QSize(0, 55))
        scrollArea.setFrameShape(QFrame.Shape.Box)  # -> NoFrame maybe?
        scrollArea.setWidgetResizable(True)
        scrollArea.setAlignment(Qt.AlignmentFlag.AlignLeading |
                                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        return scrollArea

    def openSingleWindow(self, windowReference: str):
        if windowReference in self._singleWindows:
            self._singleWindows[windowReference].raise_()
            self._singleWindows[windowReference].activateWindow()
        else:
            window = None
            match windowReference:
                case "LogWindow":
                    window = ui.LogWindow(LoggerClass.getRootLogger())
                case "ProgramSettingsDialog":
                    window = ui.ProgramSettingsDialog()
            if window:
                window.destroyed.connect(
                    partial(self.closedSingleWindow, windowReference))
                window.show()
                self._singleWindows[windowReference] = window
        logger.debug(self._singleWindows)

    def closedSingleWindow(self, windowReference):
        logger.debug(f"closed window {windowReference}")
        if windowReference in self._singleWindows:
            del self._singleWindows[windowReference]
        logger.debug(self._singleWindows)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event (QCloseEvent  |  None]): The qt event.
        """

        logger.debug(f"closeEvent in {__class__.__name__}")

        for window in self._singleWindows.values():
            window.close()


class HardwareEspRow(QFrame):
    """ A independent hardware row inside the scroll area """

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        self.setupUi()

    def setupUi(self):
        self.setEnabled(True)
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setLineWidth(1)

        self.selfLayout = QVBoxLayout(self)

        self.hl_espTopRow = QHBoxLayout()
        # self.hl_espTopRow.setSizeConstraint(QLayout.SetMinimumSize)

        # all size policys that we need
        sizePolicy_FixedMaximum = QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        sizePolicy_PreferredMaximum = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # all fonts that we need
        font10 = QFont()
        font10.setPointSize(10)
        font11 = QFont()
        font11.setPointSize(11)

        # The connection status label (symbol)
        self.lb_espCon = QLabel(self)
        self.lb_espCon.setSizePolicy(sizePolicy_FixedMaximum)
        self.lb_espCon.setText("\u2705")
        self.hl_espTopRow.addWidget(self.lb_espCon)

        # The esp name, mac and ip label
        self.lb_espIdMac = QLabel(self)
        self.lb_espIdMac.setSizePolicy(sizePolicy_PreferredMaximum)
        self.lb_espIdMac.setFont(font10)
        self.lb_espIdMac.setText("ESP 1 (aa:ff:aa:ff:aa:ff/192.168.1.1)")
        self.hl_espTopRow.addWidget(self.lb_espIdMac)

        # the esp wifi rssi label
        self.lb_espRssi = QLabel(self)
        self.lb_espRssi.setSizePolicy(sizePolicy_PreferredMaximum)
        self.lb_espRssi.setFont(font10)
        self.lb_espRssi.setText("Wifi: 50dbm")
        self.hl_espTopRow.addWidget(self.lb_espRssi)

        # the esp battery level label
        self.lb_espBat = QLabel(self)
        self.lb_espBat.setSizePolicy(sizePolicy_PreferredMaximum)
        self.lb_espBat.setFont(font10)
        self.lb_espBat.setText("Battery: 3.3V")
        self.hl_espTopRow.addWidget(self.lb_espBat)

        # spacer
        self.spc_espRow_1 = QSpacerItem(
            10, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.hl_espTopRow.addItem(self.spc_espRow_1)

        # the button to create/destroy the control sub-widget
        self.bt_espExpand = ui.ToggleButton(
            ("\u02C5", "\u02C4"), parent=self)
        self.bt_espExpand.setMaximumSize(QSize(40, 16777215))
        self.bt_espExpand.setFont(font11)
        self.bt_espExpand.setToolTip("Expand")
        self.hl_espTopRow.addWidget(self.bt_espExpand)

        # button to open the esp settings dialog
        self.bt_openEspSettings = QPushButton(self)
        self.bt_openEspSettings.setMaximumSize(QSize(40, 16777215))
        self.bt_openEspSettings.setFont(font11)
        self.bt_openEspSettings.setToolTip("Configure")
        self.bt_openEspSettings.setText("\ud83d\udd27")
        self.hl_espTopRow.addWidget(self.bt_openEspSettings)

        self.selfLayout.addLayout(self.hl_espTopRow)


if __name__ == "__main__":
    logger.error("There is no point running this file directly")
