"""The main application settings window
"""

from PyQt6.QtWidgets import (QComboBox, QDialogButtonBox, QWidget,
                             QFormLayout, QLabel, QLineEdit, QSizePolicy,
                             QSpacerItem, QSpinBox)
from PyQt6.QtCore import pyqtSignal as Signal, Qt
from PyQt6.QtGui import QCloseEvent
from modules import config
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class ProgramSettingsDialog(QWidget):
    def __init__(self) -> None:
        """Initialize programm settings window
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__()

        self.setupUi()

    def setupUi(self):
        """Initialize UI elements.
        """

        # the widget and it's layout
        self.setWindowTitle("Program Settings")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(415, 164)
        self.selfLayout = QFormLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # mqtt broker ip
        self.lb_mqttBrokerIp = QLabel(self)
        self.lb_mqttBrokerIp.setObjectName("lb_mqttBrokerIp")
        self.lb_mqttBrokerIp.setText("MQTT Broker IP:")

        self.le_mqttBrokerIp = QLineEdit(self)
        self.le_mqttBrokerIp.setObjectName("le_mqttBrokerIp")
        self.le_mqttBrokerIp.setInputMask("900.900.900.900")

        self.selfLayout.addRow(self.lb_mqttBrokerIp, self.le_mqttBrokerIp)

        # vrchat osc port
        self.lb_vrcOscRxPort = QLabel(self)
        self.lb_vrcOscRxPort.setObjectName("lb_vrcOscRxPort")
        self.lb_vrcOscRxPort.setText("VRC OSC Rx Port:")

        self.sb_vrcOscRxPort = QSpinBox(self)
        self.sb_vrcOscRxPort.setObjectName("sb_vrcOscRxPort")
        self.sb_vrcOscRxPort.setMaximum(65535)

        self.selfLayout.addRow(self.lb_vrcOscRxPort, self.sb_vrcOscRxPort)

        # main tps
        self.lb_tps = QLabel(self)
        self.lb_tps.setObjectName("lb_tps")
        self.lb_tps.setText("TPS:")

        self.sb_tps = QSpinBox(self)
        self.sb_tps.setObjectName("sb_tps")
        self.sb_tps.setMinimum(1)
        self.sb_tps.setMaximum(100)
        self.sb_tps.setValue(40)

        self.selfLayout.addRow(self.lb_tps, self.sb_tps)

        # log level
        self.lb_debugLevel = QLabel(self)
        self.lb_debugLevel.setObjectName("lb_debugLevel")
        self.lb_debugLevel.setText("Log Level:")

        self.cb_logLevel = QComboBox(self)
        for level in LoggerClass.getLoggingLevelStrings():
            self.cb_logLevel.addItem(level)
        self.cb_logLevel.setObjectName("cb_logLevel")

        self.selfLayout.addRow(self.lb_debugLevel, self.cb_logLevel)

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

    # handle the close event for the log window
    def closeEvent(self, event: [QCloseEvent | None]) -> None:
        """Handle window close event cleanly.

        Args:
            event (QCloseEvent  |  None]): The qt event.
        """

        logger.info(f"closeEvent in {__class__.__name__}")
