"""The main application window."""

import webbrowser
from functools import partial

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QScrollArea, QSizePolicy, QSlider,
                             QSpacerItem, QSplitter, QVBoxLayout, QWidget)

import ui
from modules import ContactGroup, HardwareDevice, ServerSingleton, config
from ui import ContactGroupSettings, EspSettingsDialog
from ui.Visualizers import VisualizerFactory
from ui.UiHelpers import handleDeletePrompt
from utils import HardwareConnectionType, LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._singleWindows: dict[str, QWidget] = {}
        self._hwRows: dict[int, QWidget] = {}
        self._cgRows: dict[int, QWidget] = {}

        self.setupUi()

        # Connect handlers for backend changes
        self.server = ServerSingleton.getInstance()
        self.server.hwManager.hwListChanged.connect(
            self._handleHwListChange)
        self.server.contactGroupManager.contactGroupListChanged.connect(
            self._handleCgListChange
        )

        # Handle add new * buttons
        self.bt_addContactGroup.clicked.connect(
            self.server.contactGroupManager.createEmptyGroup)
        self.bt_addHardwareDevice.clicked.connect(
            self.server.hwManager.createEmptyDevice)

        # Populate the HardwareDevice and ContactGroup lists
        self._pollHwList()
        self._pollCgList()

    def setupUi(self) -> None:
        """Initialize the main UI."""
        # the widget and it's layout
        self.setWindowTitle("VRC-patpatpat")
        self.resize(QSize(800, 200))
        self.setMaximumWidth(2000)
        self.setMinimumWidth(600)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.setSizePolicy(sizePolicy)
        self.theCentralWidet = QWidget(self)
        self.selfLayout = QVBoxLayout(self.theCentralWidet)

        # the splitter for the data rows
        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.splitter.setOpaqueResize(False)
        self.splitter.setChildrenCollapsible(False)

        # the top bar horizontal layout
        self.hl_topBar = QHBoxLayout()

        # hardware row label
        self.lb_espRowHeader = QLabel(self)
        self.lb_espRowHeader.setText("Hardware:")
        self.hl_topBar.addWidget(self.lb_espRowHeader)

        # add HardwareDevice button
        self.bt_addHardwareDevice = QPushButton(self)
        self.bt_addHardwareDevice.setMaximumWidth(130)
        self.bt_addHardwareDevice.setToolTip("Create new Hardware Device")
        self.bt_addHardwareDevice.setText("+ Hardware Device")
        # self.bt_addHardwareDevice.setEnabled(False)
        self.hl_topBar.addWidget(self.bt_addHardwareDevice)

        # add ContactGroup button
        self.bt_addContactGroup = QPushButton(self)
        self.bt_addContactGroup.setMaximumWidth(130)
        self.bt_addContactGroup.setToolTip("Create new Contact Group")
        self.bt_addContactGroup.setText("+ Contact Group")
        self.hl_topBar.addWidget(self.bt_addContactGroup)

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

        self.hardwareAreaWidgetContent = QWidget(self)
        self.hardwareAreaWidgetContent.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        self.hardwareAreaWidgetContentLayout = QVBoxLayout(
            self.hardwareAreaWidgetContent)
        self.hardwareAreaWidgetContentLayout.setContentsMargins(
            0, 0, 0, 0)
        self.splitter.addWidget(self.hardwareAreaWidgetContent)

        # contact group label
        self.lb_groupRowHeader = QLabel(self)
        self.lb_groupRowHeader.setText("Contact Groups:")
        self.lb_groupRowHeader.setMaximumHeight(25)
        self.splitter.addWidget(self.lb_groupRowHeader)

        self.contactGroupAreaWidgetContent = QWidget(self)
        self.contactGroupAreaWidgetContentLayout = QVBoxLayout(
            self.contactGroupAreaWidgetContent)
        self.contactGroupAreaWidgetContentLayout.setContentsMargins(
            0, 0, 0, 0)
        self.splitter.addWidget(self.contactGroupAreaWidgetContent)

        # add layout to central widget to mainwindow
        self.selfLayout.addWidget(self.splitter)
        self.theCentralWidet.setLayout(self.selfLayout)
        self.setCentralWidget(self.theCentralWidet)

    def openSingleWindow(self, windowReference: str) -> None:
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
        logger.debug(f"Current windows: {str(self._singleWindows)}")

    def closedSingleWindow(self, windowReference) -> None:
        logger.debug(f"Closed window {windowReference}")
        if windowReference in self._singleWindows:
            del self._singleWindows[windowReference]
        logger.debug(f"Current windows: {str(self._singleWindows)}")

    def _pollHwList(self) -> None:
        """Trigger initial HardwareDevice row loading after startup"""
        self._handleHwListChange(self.server.hwManager.hardwareDevices)

    def _handleHwListChange(self, devices: dict[int, HardwareDevice]) -> None:
        """Handle changes to the servers hardware list.
        This could be a new device beeing added or
        an existing one re-created.

        Args:
            devices (dict[int, HardwareDevice]): The hardwareDevices dict.
        """
        for id, row in self._hwRows.items():
            row.close()
            row.deleteLater()
        self._hwRows = {}
        for id, device in devices.items():
            newRow = HardwareEspRow(device._configKey,
                                    self.server.hwManager.hardwareDevices[id],
                                    self.hardwareAreaWidgetContent)
            device.uiBatteryStateChanged.connect(newRow.lb_espBat.setFloat)
            device.uiRssiStateChanged.connect(newRow.lb_espRssi.setNum)
            device.deviceConnectionChanged.connect(newRow.lb_espCon.setState)
            self.hardwareAreaWidgetContentLayout.addWidget(newRow)
            self._hwRows[id] = newRow

    def _pollCgList(self) -> None:
        """Trigger initial ContactGroup row loading after startup"""
        self._handleCgListChange(self.server.contactGroupManager.contactGroups)

    def _handleCgListChange(self, groups: dict[int, ContactGroup]) -> None:
        """Handle changes to the ContactGroup list.

        Args:
            groups (list[ContactGroup]): The list of ContactGroups
        """
        for id, row in self._cgRows.items():
            row.close()
            row.deleteLater()
        self._cgRows = {}
        for id, group in groups.items():
            newRow = ContactGroupRow(group._configKey,
                                     self.server.contactGroupManager.contactGroups[id],
                                     self.contactGroupAreaWidgetContent)
            group.dataRxStateChanged.connect(
                newRow.lb_groupHasIncomingData.setState)
            newRow.hsld_strength.valueChanged.connect(
                group.strengthSliderValueChanged)
            group.openSettings.connect(newRow.openSettingsWindow)
            self.contactGroupAreaWidgetContentLayout.addWidget(
                newRow)
            self._cgRows[id] = newRow

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event (QCloseEvent  |  None]): The qt event.
        """
        logger.debug("-----EXIT STARTED-----")
        logger.debug(f"closeEvent in {__class__.__name__}")

        logger.debug("Closing windows")
        for window in self._singleWindows.values():
            window.close()

        for hwRow in self._hwRows.values():
            hwRow.close()

        for cgRow in self._cgRows.values():
            cgRow.close()

        logger.debug("Stopping server...")
        self.server.stop()


class BaseRow(QFrame):
    """The base for hardware and group rows with an expandable row."""
    widgetExpansionStateChanged = QSignal(bool)

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        self.expandingWidget = None
        self._settingsWindow: QWidget | None = None
        self.buildCommonUi()
        self.buildUi()

    def buildCommonUi(self) -> None:
        self.setEnabled(True)
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setLineWidth(1)
        self.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

        self.selfLayout = QVBoxLayout(self)

    def buildUi(self) -> None:
        raise NotImplementedError

    def createExpandingWidget(self, instance: QWidget) -> None:
        self.expandingWidget = instance
        self.selfLayout.addWidget(instance)
        self.widgetExpansionStateChanged.emit(True)

    def _deleteExpandingWidget(self) -> None:
        if self.expandingWidget:
            self.selfLayout.removeWidget(self.expandingWidget)
            self.expandingWidget.close()
            self.expandingWidget = None
            self.widgetExpansionStateChanged.emit(False)

    @QSlot()
    def _openSettingsWindow(self,
                            win: type[ContactGroupSettings] |
                            type[EspSettingsDialog], configKey: str):
        if self._settingsWindow:
            self._settingsWindow.raise_()
            self._settingsWindow.activateWindow()
        else:
            self._settingsWindow = win(configKey)
            self._settingsWindow.destroyed.connect(
                self._closedSettingsWindow)
            self._settingsWindow.setWindowModality(
                Qt.WindowModality.ApplicationModal)
            self._settingsWindow.show()

    def _closedSettingsWindow(self):
        self._settingsWindow = None

    def _lockSlider(self) -> None:
        self.sliderLocked = True

    def _unlockSlider(self) -> None:
        self.sliderLocked = False

    def close(self) -> None:
        """Close any windows that might be open"""
        super().close()


class ExpandedWidgetDataRowBase(QHBoxLayout):
    """ The base for the expanding widgets """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

        self.buildCommonUi()
        self.buildUi()

    def buildCommonUi(self) -> None:
        self.setContentsMargins(8, 0, -1, 2)

    def buildUi(self) -> None:
        raise NotImplementedError

    def updateValue(self) -> None:
        raise NotImplementedError

    def _lockSlider(self) -> None:
        logger.debug("Slider locked")
        self.sliderLocked = True

    def _unlockSlider(self) -> None:
        logger.debug("Slider unlocked")
        self.sliderLocked = False


class HardwareEspRow(BaseRow):
    """A independent hardware row inside the scroll area."""

    def __init__(self, configKey: str, deviceRef: HardwareDevice,
                 parent: QWidget | None) -> None:
        self._configKey = configKey
        super().__init__(parent)
        self._deviceRef = deviceRef

        self._updateStaticText()

    def buildUi(self) -> None:
        self.hl_espTopRow = QHBoxLayout()

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
        self.lb_espCon = ui.StatefulLabel(("\u2716", "\u2705", "\u231B"), self)
        self.lb_espCon.setSizePolicy(sizePolicy_FixedMaximum)
        self.lb_espCon.setState(2)
        self.hl_espTopRow.addWidget(self.lb_espCon)

        # The esp name, mac and ip label
        self.lb_espIdMac = ui.StaticLabel(
            "ESP ", "", "", self)
        self.lb_espIdMac.setSizePolicy(sizePolicy_PreferredMaximum)
        self.lb_espIdMac.setFont(font10)
        self.hl_espTopRow.addWidget(self.lb_espIdMac)

        # the esp wifi rssi label
        self.lb_espRssi = ui.StaticLabel("Wifi: ", "-", " dbm", self)
        self.lb_espRssi.setSizePolicy(sizePolicy_PreferredMaximum)
        self.lb_espRssi.setFont(font10)
        self.hl_espTopRow.addWidget(self.lb_espRssi)

        # the esp battery level label
        self.lb_espBat = ui.StaticLabel("Battery: ", "- ", " V", self)
        self.lb_espBat.setSizePolicy(sizePolicy_PreferredMaximum)
        self.lb_espBat.setFont(font10)
        self.hl_espTopRow.addWidget(self.lb_espBat)

        # spacer
        self.spc_espRow_1 = QSpacerItem(
            10, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.hl_espTopRow.addItem(self.spc_espRow_1)

        # the button to create/destroy the control sub-widget
        self.bt_espExpand = ui.ToggleButton(
            ("\u02C5", "\u02C4"), parent=self)
        self.bt_espExpand.setMaximumWidth(40)
        self.bt_espExpand.setFont(font11)
        self.bt_espExpand.setToolTip("Expand")
        self.bt_espExpand.toggledOn.connect(self._openExpandingWidget)
        self.bt_espExpand.toggledOff.connect(self._deleteExpandingWidget)
        self.hl_espTopRow.addWidget(self.bt_espExpand)

        # button to delete HardwareDevice
        self.bt_deleteDevice = QPushButton(self)
        self.bt_deleteDevice.setMaximumWidth(40)
        self.bt_deleteDevice.setFont(font11)
        self.bt_deleteDevice.setToolTip("Delete Hardware Device")
        self.bt_deleteDevice.setText("\u274C")
        self.bt_deleteDevice.clicked.connect(self._handleDeviceDelete)
        self.hl_espTopRow.addWidget(self.bt_deleteDevice)

        # button to open the esp settings dialog
        self.bt_openEspSettings = QPushButton(self)
        self.bt_openEspSettings.setMaximumWidth(40)
        self.bt_openEspSettings.setFont(font11)
        self.bt_openEspSettings.setToolTip("Configure")
        self.bt_openEspSettings.setText("\ud83d\udd27")
        self.bt_openEspSettings.clicked.connect(
            partial(self._openSettingsWindow,
                    EspSettingsDialog, self._configKey))
        self.hl_espTopRow.addWidget(self.bt_openEspSettings)

        self.selfLayout.addLayout(self.hl_espTopRow)

    def _updateStaticText(self) -> None:
        id = config.get(f"{self._configKey}.id")
        name = config.get(f"{self._configKey}.name")
        mac = config.get(f"{self._configKey}.wifiMac")
        connType = config.get(f"{self._configKey}.connectionType")
        connAddr = config.get(f"{self._configKey}.lastIp") if \
            connType == HardwareConnectionType.OSC else \
            config.get(f"{self._configKey}.serialPort")
        self.lb_espIdMac.setText(f"{id} '{name}' ({mac}/{connAddr})")

    def _openExpandingWidget(self) -> None:
        """Create the expanding widget and initialize it."""
        widget = EspMoreInfoWidget(self)
        widget.connect(self._deviceRef)
        self.createExpandingWidget(widget)

    def _handleDeviceDelete(self) -> None:
        group = config.get(self._configKey)
        if group:
            delete = handleDeletePrompt(self,
                                        f"Hardware Device ID: {group["id"]}"
                                        f" Name: {group["name"]}")
            if delete:
                logger.debug(f"Deleting {self._configKey}")
                config.delete(self._configKey)


class EspMoreInfoWidget(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize EspMoreInfoWidget."""
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)
        self.buildUi()

    def buildUi(self) -> None:
        self.selfLayout = QVBoxLayout(self)
        self.setContentsMargins(-1, -1, -1, 0)
        self.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum))

        # the spacing line
        self.line = QFrame(self)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.selfLayout.addWidget(self.line)

        # the motors label
        self.lb_motorsRow = ui.StaticLabel("Motors: ", "", "", self)
        self.selfLayout.addWidget(self.lb_motorsRow)

        # a horizontal row for the buttons
        self.bottomButtonRow = QHBoxLayout()
        # the stop app button
        self.bt_stopAllMotors = QPushButton(self)
        self.bt_stopAllMotors.setMaximumWidth(60)
        self.bt_stopAllMotors.setText("Stop all")
        self.bottomButtonRow.addWidget(
            self.bt_stopAllMotors, 0, Qt.AlignmentFlag.AlignLeft)

        self.selfLayout.addLayout(self.bottomButtonRow)

    def connect(self, device: HardwareDevice) -> None:
        """Connect device with expanded row.

        Args:
            device (HardwareDevice): The device reference
        """
        self.rows: list[HardwareMotorChannelRow] = []
        for channelId in range(device._numMotors):
            row = HardwareMotorChannelRow(channelId)
            row.sliderValueChanged.connect(device.setAndSendPinValues)
            self.selfLayout.addLayout(row)
            self.rows.append(row)
        device.motorDataSent.connect(self._handleMotorData)
        self.bt_stopAllMotors.clicked.connect(device.resetAllPinStates)

    def _handleMotorData(self, values: list[int]) -> None:
        """Writes the list of PWM values into the slider rows.

        Args:
            values (list): The list of PWM values.
        """
        try:
            for i, row in enumerate(self.rows):
                row.updateValue(values[i])
        except IndexError:
            pass

    # handle the close event
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event QCloseEvent): The QCloseEvent.
        """
        logger.debug(f"closeEvent in {__class__.__name__}")


class HardwareMotorChannelRow(ExpandedWidgetDataRowBase):
    sliderValueChanged = QSignal(int, int)

    def __init__(self, rowId: int, *args, **kwargs) -> None:
        """Initialize HardwareMotorChannelRow."""
        self.rowId = rowId
        self.sliderLocked = False
        super().__init__(*args, **kwargs)

    def buildUi(self) -> None:
        # Motor number
        self.lb_motorNum = ui.StaticLabel("Channel ", str(self.rowId))
        self.addWidget(self.lb_motorNum)

        # the pwm slider
        self.hsld_motorVal = QSlider(Qt.Orientation.Horizontal)
        self.hsld_motorVal.setMinimumSize(QSize(100, 0))
        self.hsld_motorVal.setMaximum(255)
        self.hsld_motorVal.setValue(0)
        self.hsld_motorVal.setTracking(True)
        self.addWidget(self.hsld_motorVal)

        # the pwm number
        self.lb_motorVal = ui.StaticLabel("PWM: ", "0")
        self.addWidget(self.lb_motorVal)

        # enable slider locking while mouse has it grabbed
        self.hsld_motorVal.sliderPressed.connect(self._lockSlider)
        self.hsld_motorVal.sliderReleased.connect(self._unlockSlider)
        # connect slider value event
        self.hsld_motorVal.valueChanged.connect(self._sliderValueChanged)

    # handle the close event
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event QCloseEvent): The QCloseEvent.
        """
        logger.debug(f"closeEvent in {__class__.__name__}")

    @QSlot(int)
    def _sliderValueChanged(self, value: int) -> None:
        """Add the channelId to the slider value change event.

        Args:
            value (int): The sliders PWM value.
        """
        if self.sliderLocked:
            self.sliderValueChanged.emit(self.rowId, value)

    def updateValue(self, value: int) -> None:
        """Sets the slider and it's label to a new value.
        Slider value is only set when slider is not currently grabbed.
        Slider range is automatically extended.

        Args:
            value (int): The new PWM value to set the slider to.
        """
        self.lb_motorVal.setNum(value)
        if not self.sliderLocked:
            if value > self.hsld_motorVal.maximum():
                self.hsld_motorVal.setMaximum(value)
            self.hsld_motorVal.setValue(value)


class ContactGroupRow(BaseRow):
    """A independent contact group row inside the scroll area."""
    strengthSliderValueChanged = QSignal(int, int)

    def __init__(self, configKey: str, contactGroupRef: ContactGroup,
                 parent: QWidget | None) -> None:
        self._configKey = configKey
        self._visualizerWindow: QWidget | None = None
        self.visualizerType = VisualizerFactory.fromType(
            contactGroupRef.solver.getType())
        super().__init__(parent)
        self._contactGroupRef = contactGroupRef

        self._updateStaticText()

    def buildUi(self) -> None:
        self.hl_groupTopRow = QHBoxLayout()

        # all fonts that we need
        font11 = QFont()
        font11.setPointSize(11)

        # the name label
        self.lb_contactGroupName = ui.StaticLabel("Name: ", "", "", self)
        # self.lb_contactGroupName.setScaledContents(True)
        self.hl_groupTopRow.addWidget(self.lb_contactGroupName)

        # the vrc data label
        self.lb_groupHasIncomingData = ui.StatefulLabel(
            ("VRC Data: \u274C", "VRC Data: \u2705", "VRC Data: \u231B"), self)
        self.lb_groupHasIncomingData.setState(2)

        self.hl_groupTopRow.addWidget(self.lb_groupHasIncomingData)

        # the strength slider
        self.hsld_strength = QSlider(Qt.Orientation.Horizontal)
        self.hsld_strength.setMinimumSize(QSize(100, 0))
        self.hsld_strength.setMinimum(0)
        self.hsld_strength.setMaximum(100)
        self.hsld_strength.setTracking(True)
        self.hl_groupTopRow.addWidget(self.hsld_strength)

        # the strength number
        self.lb_strength = ui.StaticLabel("Strength: ", "-", "%")
        self.hsld_strength.valueChanged.connect(self.lb_strength.setNum)
        self.hl_groupTopRow.addWidget(self.lb_strength)

        # spacer
        self.spc_groupRow_1 = QSpacerItem(
            10, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.hl_groupTopRow.addItem(self.spc_groupRow_1)

        # the group info expand button
        self.bt_groupExpand = ui.ToggleButton(
            ("\u02C5", "\u02C4"), parent=self)
        self.bt_groupExpand.setMaximumWidth(40)
        self.bt_groupExpand.setFont(font11)
        self.bt_groupExpand.setToolTip("Expand")
        self.bt_groupExpand.toggledOn.connect(self._openExpandingWidget)
        self.bt_groupExpand.toggledOff.connect(
            self._deleteExpandingWidget)
        self.hl_groupTopRow.addWidget(self.bt_groupExpand)

        if self.visualizerType:
            # the open visualizer button if supported
            self.bt_openVisualizer = QPushButton(self)
            self.bt_openVisualizer.setMaximumWidth(40)
            self.bt_openVisualizer.setFont(font11)
            self.bt_openVisualizer.setToolTip("Open visualizer")
            self.bt_openVisualizer.setText("\ud83d\udcc8")
            self.bt_openVisualizer.clicked.connect(self._openVisualizerWindow)
            self.hl_groupTopRow.addWidget(self.bt_openVisualizer)

        # button to delete ContactGroup
        self.bt_deleteGroup = QPushButton(self)
        self.bt_deleteGroup.setMaximumWidth(40)
        self.bt_deleteGroup.setFont(font11)
        self.bt_deleteGroup.setToolTip("Delete Contact Group")
        self.bt_deleteGroup.setText("\u274C")
        self.bt_deleteGroup.clicked.connect(self._handleGroupDelete)
        self.hl_groupTopRow.addWidget(self.bt_deleteGroup)

        # button to open the group settings dialog
        self.bt_openGroupSettings = QPushButton(self)
        self.bt_openGroupSettings.setMaximumWidth(40)
        self.bt_openGroupSettings.setFont(font11)
        self.bt_openGroupSettings.setToolTip("Configure")
        self.bt_openGroupSettings.setText("\ud83d\udd27")
        self.bt_openGroupSettings.clicked.connect(self.openSettingsWindow)
        self.hl_groupTopRow.addWidget(self.bt_openGroupSettings)

        self.selfLayout.addLayout(self.hl_groupTopRow)

    def _updateStaticText(self) -> None:
        name = config.get(f"{self._configKey}.name", "")
        self.lb_contactGroupName.setText(name)
        strength = config.get(f"{self._configKey}.solver.strength", 69)
        self.hsld_strength.setValue(strength)
        self.lb_strength.setNum(strength)

    def openSettingsWindow(self) -> None:
        self._openSettingsWindow(ContactGroupSettings, self._configKey)

    def _openVisualizerWindow(self) -> None:
        if self._visualizerWindow:
            self._visualizerWindow.raise_()
            self._visualizerWindow.activateWindow()
        elif self.visualizerType:
            self._visualizerWindow = self.visualizerType(
                self._contactGroupRef)
            self._visualizerWindow.destroyed.connect(
                self._closedVisualizerWindow)
            self._contactGroupRef.newPointSolved.connect(
                self._visualizerWindow.visualizer.handleDataPoint)
            self._visualizerWindow.show()

    def _closedVisualizerWindow(self):
        self._visualizerWindow = None

    def _openExpandingWidget(self) -> None:
        """Create the expanding widget and initialize it.
        """
        widget = ContactGroupPointsWidget(self)
        widget.connect(self._contactGroupRef)
        self.createExpandingWidget(widget)

    def _handleGroupDelete(self) -> None:
        group = config.get(self._configKey)
        if group:
            delete = handleDeletePrompt(self,
                                        f"Contact Group ID: {group["id"]}"
                                        f" Name: {group["name"]}")
            if delete:
                logger.debug(f"Deleting {self._configKey}")
                config.delete(self._configKey)

    def close(self) -> None:
        if self._visualizerWindow:
            self._visualizerWindow.close()
        super().close()


class ContactGroupPointsWidget(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize ContactGroupPointsWidget."""
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.buildUi()

    def buildUi(self) -> None:
        self.selfLayout = QVBoxLayout(self)
        self.setContentsMargins(-1, -1, -1, 0)
        self.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum))

        # the spacing line
        self.line = QFrame(self)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.selfLayout.addWidget(self.line)

        # the points label
        self.lb_pointsRow = QLabel(self)
        self.lb_pointsRow.setText("Points:")
        self.selfLayout.addWidget(self.lb_pointsRow)

    def connect(self, contactGroup: ContactGroup) -> None:
        """Connect contact group row with expanded row.

        Args:
            contactGroup (ContactGroup): The contact group reference
        """
        self.rows: list[PointDetailsRow] = []
        for motor in contactGroup.motors:
            row = PointDetailsRow(motor._name)
            motor.speedChanged.connect(row.updateValue)
            self.selfLayout.addLayout(row)
            self.rows.append(row)

    # handle the close event
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event QCloseEvent): The QCloseEvent.
        """
        logger.debug(f"closeEvent in {__class__.__name__}")


class PointDetailsRow(ExpandedWidgetDataRowBase):
    def __init__(self, name: str, *args, **kwargs) -> None:
        """Initialize PointDetailsRow."""
        logger.debug(f"Creating {__class__.__name__}")
        self._name = name
        super().__init__(*args, **kwargs)

    def buildUi(self) -> None:
        self.lb_groupPointName = ui.StaticLabel(
            "Name: ", self._name, parent=self.parent())
        self.addWidget(self.lb_groupPointName, 0, Qt.AlignmentFlag.AlignLeft)
        self.lb_groupPointValue = ui.StaticLabel(
            "Value: ", "-", parent=self.parent())
        self.addWidget(self.lb_groupPointValue, 0, Qt.AlignmentFlag.AlignLeft)
        self.addStretch(1)

    def updateValue(self, a1: int, a2: int, value: float) -> None:
        self.lb_groupPointValue.setFloat(value)


if __name__ == "__main__":
    print("There is no point running this file directly")
