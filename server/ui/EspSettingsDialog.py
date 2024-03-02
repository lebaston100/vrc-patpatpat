"""The ESP settings window
"""

from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QComboBox, QDialogButtonBox, QFormLayout,
                             QLineEdit, QSizePolicy, QSpacerItem, QSpinBox,
                             QWidget)

from modules import OptionAdapter, config
from ui.UiHelpers import handleClosePrompt
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class EspSettingsDialog(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Initialize esp settings window"""

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey
        self.buildUi()

        # after UI is setup load options into ui elements
        self.loadOptsToGui(config, self._configKey)

    def buildUi(self) -> None:
        """Initialize UI elements."""
        # the widget and it's layout
        self.setWindowTitle("ESP Settings")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(400, 200)
        self.selfLayout = QFormLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # ID
        self.sb_espId = QSpinBox(self)
        self.sb_espId.setObjectName("sb_espId")
        self.sb_espId.setEnabled(False)
        self.addOpt("id", self.sb_espId, int)

        self.selfLayout.addRow("ID:", self.sb_espId)

        # Name
        self.le_espName = QLineEdit(self)
        self.le_espName.setObjectName("le_espName")
        self.le_espName.setMaxLength(30)
        self.addOpt("name", self.le_espName)

        self.selfLayout.addRow("Name:", self.le_espName)

        # Connection type
        self.cb_connectionType = QComboBox(self)
        self.cb_connectionType.addItem("OSC")
        self.cb_connectionType.addItem("SlipSerial")
        self.cb_connectionType.setCurrentText("OSC")
        # self.cb_connectionType.setEnabled(False)
        self.addOpt("connectionType", self.cb_connectionType)

        self.selfLayout.addRow("Connection Type:", self.cb_connectionType)

        # Number of motors
        self.sb_espNumMotors = QSpinBox(self)
        self.sb_espNumMotors.setObjectName("sb_espNumMotors")
        self.sb_espNumMotors.setMinimum(1)
        self.addOpt("numMotors", self.sb_espNumMotors, int)

        self.selfLayout.addRow("Number of motors:", self.sb_espNumMotors)

        # Serial port name
        self.le_serialPort = QLineEdit(self)
        self.le_serialPort.setObjectName("le_serialPort")
        self.le_serialPort.setEnabled(False)
        self.le_serialPort.setReadOnly(True)
        self.addOpt("serialPort", self.le_serialPort)

        self.selfLayout.addRow("Serial Port:", self.le_serialPort)

        # Last Device IP
        self.le_espLastIp = QLineEdit(self)
        self.le_espLastIp.setObjectName("le_espLastIp")
        self.le_espLastIp.setEnabled(False)
        self.le_espLastIp.setReadOnly(True)
        self.addOpt("lastIp", self.le_espLastIp)

        self.selfLayout.addRow("Last Device IP:", self.le_espLastIp)

        # Device MAC
        self.le_espMac = QLineEdit(self)
        self.le_espMac.setObjectName("le_espMac")
        self.le_espMac.setInputMask("Hh:Hh:Hh:Hh:Hh:Hh")
        self.addOpt("wifiMac", self.le_espMac)

        self.selfLayout.addRow("Device MAC:", self.le_espMac)

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
        """Handle save button press."""
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
