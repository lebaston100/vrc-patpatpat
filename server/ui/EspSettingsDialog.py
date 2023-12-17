"""The ESP settings window
"""

from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
                             QSizePolicy, QSpacerItem, QSpinBox, QWidget)

from modules import OptionAdapter, config
from ui.uiHelpers import handleCloseEvent
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class EspSettingsDialog(QWidget, OptionAdapter):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize esp settings window
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.buildUi()
        self._configKey = "TBD"

        # TODO: This is an issue because one of the options is the a subkey.
        # we need a way for this window so find out which esp is belongs to
        # so we can solve that then
        # maybe we extend the normal get/set methods for the global config
        # do that it can also deal with the paths

        # after UI is setup load options into ui elements
        # self.loadOptsToGui(config.get(self._configKey))

    def buildUi(self):
        """Initialize UI elements.
        """

        # the widget and it's layout
        self.setWindowTitle("ESP Settings")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(396, 195)
        self.selfLayout = QFormLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # ID
        self.sb_espId = QSpinBox(self)
        self.sb_espId.setObjectName("sb_espId")

        self.selfLayout.addRow("ID:", self.sb_espId)

        # Name
        self.le_espName = QLineEdit(self)
        self.le_espName.setObjectName("le_espName")
        self.le_espName.setMaxLength(30)

        self.selfLayout.addRow("Name:", self.le_espName)

        # Number of motors
        self.sb_espNumMotors = QSpinBox(self)
        self.sb_espNumMotors.setObjectName("sb_espNumMotors")
        self.sb_espNumMotors.setMinimum(1)

        self.selfLayout.addRow("Number of motors:", self.sb_espNumMotors)

        # Last Device IP
        self.le_espLastIp = QLineEdit(self)
        self.le_espLastIp.setObjectName("le_espLastIp")
        self.le_espLastIp.setEnabled(False)
        self.le_espLastIp.setReadOnly(True)

        self.selfLayout.addRow("Last Device IP:", self.le_espLastIp)

        # Device MAC
        self.le_espMac = QLineEdit(self)
        self.le_espMac.setObjectName("le_espMac")
        self.le_espMac.setInputMask("Hh:Hh:Hh:Hh:Hh:Hh")

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
        logger.debug("Save button pressed")
        updatedSettings, changedPaths = self.getOptsFromGui(
            config.get(self._configKey))
        config.set(self._configKey, updatedSettings, changedPaths)
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
        updatedSettings, changedPaths = self.getOptsFromGui(
            config.get(self._configKey))
        if changedPaths:
            handleCloseEvent(self, event)


if __name__ == "__main__":
    print("There is no point running this file directly")
