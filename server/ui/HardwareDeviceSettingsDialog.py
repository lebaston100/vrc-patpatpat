"""The Hardware Device settings window
"""

from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QComboBox, QDialogButtonBox, QFormLayout,
                             QLineEdit, QSizePolicy, QSpacerItem, QSpinBox,
                             QWidget)

from modules.GlobalConfig import GlobalConfigSingleton
from modules.OptionAdapter import OptionAdapter
from ui.UiHelpers import handleClosePrompt
from utils.Logger import LoggerClass

logger = LoggerClass.getSubLogger(__name__)
config = GlobalConfigSingleton.getInstance()


class HardwareDeviceSettingsDialog(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Initialize Hardware Device settings window"""

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey
        self.buildUi()

        # after UI is setup load options into ui elements
        self.loadOptsToGui(config, self._configKey)

    def buildUi(self) -> None:
        """Initialize UI elements."""
        # the widget and it's layout
        self.setWindowTitle("Hardware Device Settings")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(400, 200)
        self.selfLayout = QFormLayout(self)

        # ID
        self.sb_hwId = QSpinBox(self)
        self.sb_hwId.setEnabled(False)
        self.addOpt("id", self.sb_hwId, int)

        self.selfLayout.addRow("ID:", self.sb_hwId)

        # Name
        self.le_hwName = QLineEdit(self)
        self.le_hwName.setMaxLength(30)
        self.addOpt("name", self.le_hwName)

        self.selfLayout.addRow("Name:", self.le_hwName)

        # Connection type
        self.cb_connectionType = QComboBox(self)
        self.cb_connectionType.addItem("OSC")
        self.cb_connectionType.addItem("SlipSerial")
        self.cb_connectionType.setCurrentText("OSC")
        # self.cb_connectionType.setEnabled(False)
        self.addOpt("connectionType", self.cb_connectionType)

        self.selfLayout.addRow("Connection Type:", self.cb_connectionType)

        # Number of motors
        self.sb_hwNumMotors = QSpinBox(self)
        self.sb_hwNumMotors.setMinimum(1)
        self.addOpt("numMotors", self.sb_hwNumMotors, int)

        self.selfLayout.addRow("Number of motors:", self.sb_hwNumMotors)

        # Serial port name
        self.le_serialPort = QLineEdit(self)
        self.le_serialPort.setEnabled(False)
        self.le_serialPort.setReadOnly(True)
        self.addOpt("serialPort", self.le_serialPort)

        self.selfLayout.addRow("Serial Port:", self.le_serialPort)

        # Last Device IP
        self.le_hwLastIp = QLineEdit(self)
        self.le_hwLastIp.setEnabled(False)
        self.le_hwLastIp.setReadOnly(True)
        self.addOpt("lastIp", self.le_hwLastIp)

        self.selfLayout.addRow("Last Device IP:", self.le_hwLastIp)

        # Device MAC
        self.le_hwMac = QLineEdit(self)
        self.le_hwMac.setInputMask("Hh:Hh:Hh:Hh:Hh:Hh")
        self.addOpt("wifiMac", self.le_hwMac)

        self.selfLayout.addRow("Device MAC:", self.le_hwMac)

        # spacer
        self.spacer1 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.selfLayout.addItem(self.spacer1)

        # save/cancel buttons
        self.bt_saveCancelButtons = QDialogButtonBox(self)
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
