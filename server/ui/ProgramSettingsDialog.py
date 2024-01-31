"""The main application settings window
"""

from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QComboBox, QDialogButtonBox, QFormLayout, QLabel,
                             QLineEdit, QSizePolicy, QSpacerItem, QSpinBox,
                             QWidget)

from modules import OptionAdapter, config
from ui.uiHelpers import handleClosePrompt
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class ProgramSettingsDialog(QWidget, OptionAdapter):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize programm settings window"""

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = "program"
        self.buildUi()

        # after UI is setup load options into ui elements
        self.loadOptsToGui(config, self._configKey)

    def buildUi(self):
        """Initialize UI elements."""

        # the widget and it's layout
        self.setWindowTitle("Program Settings")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(415, 164)
        self.selfLayout = QFormLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # mqtt broker ip
        self.le_mqttBrokerIp = QLineEdit(self)
        self.le_mqttBrokerIp.setObjectName("le_mqttBrokerIp")
        self.le_mqttBrokerIp.setInputMask("900.900.900.900")
        self.addOpt("mqttBrokerIp", self.le_mqttBrokerIp)

        self.selfLayout.addRow("MQTT Broker IP:", self.le_mqttBrokerIp)

        # vrchat osc send ip
        self.le_vrcOscReceiveAddress = QLineEdit(self)
        self.le_vrcOscReceiveAddress.setObjectName("le_vrcOscReceiveAddress")
        self.le_vrcOscReceiveAddress.setInputMask("900.900.900.900")
        self.addOpt("vrcOscReceiveAddress", self.le_vrcOscReceiveAddress)

        self.selfLayout.addRow(
            "VRC OSC Send IP:", self.le_vrcOscReceiveAddress)

        # vrchat osc send port
        self.sb_vrcOscSendPort = QSpinBox(self)
        self.sb_vrcOscSendPort.setObjectName("sb_vrcOscSendPort")
        self.sb_vrcOscSendPort.setMaximum(65535)
        self.addOpt("vrcOscSendPort", self.sb_vrcOscSendPort, dataType=int)

        self.selfLayout.addRow("VRC OSC Send Port:", self.sb_vrcOscSendPort)

        # vrchat osc receive port
        self.sb_vrcOscReceivePort = QSpinBox(self)
        self.sb_vrcOscReceivePort.setObjectName("sb_vrcOscReceivePort")
        self.sb_vrcOscReceivePort.setMaximum(65535)
        self.addOpt("vrcOscReceivePort",
                    self.sb_vrcOscReceivePort, dataType=int)

        self.selfLayout.addRow("VRC OSC Receive Port:",
                               self.sb_vrcOscReceivePort)

        # main tps
        self.sb_tps = QSpinBox(self)
        self.sb_tps.setObjectName("sb_tps")
        self.sb_tps.setMinimum(1)
        self.sb_tps.setMaximum(100)
        self.addOpt("mainTps", self.sb_tps, dataType=int)

        self.selfLayout.addRow("TPS:", self.sb_tps)

        # log level
        self.cb_logLevel = QComboBox(self)
        for level in LoggerClass.getLoggingLevelStrings():
            self.cb_logLevel.addItem(level)
        self.cb_logLevel.setObjectName("cb_logLevel")
        self.addOpt("logLevel", self.cb_logLevel)

        self.selfLayout.addRow("Log Level:", self.cb_logLevel)

        # spacer
        self.spacer1 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.selfLayout.addItem(self.spacer1)

        # save/cancel buttons
        self.bt_saveCancelButtons = QDialogButtonBox(self)
        self.bt_saveCancelButtons.setObjectName("bt_saveCancelButtons")
        self.bt_saveCancelButtons.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save)
        self.bt_saveCancelButtons.rejected.connect(self.close)
        self.bt_saveCancelButtons.accepted.connect(self.handleSaveButton)

        self.selfLayout.addRow(self.bt_saveCancelButtons)

    def handleSaveButton(self) -> None:
        logger.debug("Save button pressed")
        self.saveOptsFromGui(config, self._configKey)
        self.close()

    # handle the close event for the log window
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event QCloseEvent): The QCloseEvent.
        """

        logger.debug(f"closeEvent in {__class__.__name__}")

        # this might be removed later if it blocks processing data
        # check and warn for unsaved changes
        changedPaths = self.saveOptsFromGui(config, self._configKey, True)
        if changedPaths:
            handleClosePrompt(self, event)


if __name__ == "__main__":
    print("There is no point running this file directly")
