"""The contact group settings window
"""

from copy import deepcopy
import random
from typing import Any, cast

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QSize, Qt, QVariant
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QCheckBox,
                             QComboBox, QDialogButtonBox, QFormLayout, QFrame,
                             QHBoxLayout, QHeaderView, QLineEdit, QPushButton,
                             QSizePolicy, QSpacerItem, QSpinBox, QTableView,
                             QTabWidget, QVBoxLayout, QWidget)

from modules.GlobalConfig import GlobalConfigSingleton
from modules.OptionAdapter import OptionAdapter
from ui.Delegates import (LineEditMoreButtonDelegate, FloatSpinBoxDelegate,
                          IntSpinBoxDelegate)
from ui.UiHelpers import handleClosePrompt, handleDeletePrompt
from utils.Enums import SolverType
from utils.Logger import LoggerClass
from utils.PathReader import PathReader
from utils.VrcAvatarsLoader import getVrcAvatars, vrcInternals

logger = LoggerClass.getSubLogger(__name__)
config = GlobalConfigSingleton.getInstance()


class ContactGroupSettings(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Initialize contact settings window."""

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey

        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements.
        All tabs are in their own subclasses.
        """
        # the widget and it's layout
        self.setWindowTitle("Contact Group Settings")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(980, 500)
        self.selfLayout = QVBoxLayout(self)

        # the tab widget
        self.mainTabWidget = QTabWidget(self)

        # add all 4 tabs to the tab widget
        self.tab_general = TabGeneral(self._configKey)
        self.mainTabWidget.addTab(self.tab_general, "General")

        self.tab_motors = TabMotors(self._configKey)
        self.mainTabWidget.addTab(self.tab_motors, "Motors")

        self.tab_contactPoints = TabContactPoints(self._configKey)
        self.mainTabWidget.addTab(self.tab_contactPoints, "Contact Points")

        self.tab_solver = TabSolver(self._configKey)
        self.mainTabWidget.addTab(self.tab_solver, "Solver")

        self.mainTabWidget.setCurrentIndex(0)
        self.selfLayout.addWidget(self.mainTabWidget)

        # save/cancel buttons
        self.bt_saveCancelButtons = QDialogButtonBox(self)
        self.bt_saveCancelButtons.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save)
        self.bt_saveCancelButtons.rejected.connect(self.close)
        self.bt_saveCancelButtons.accepted.connect(self.handleSaveButton)

        self.selfLayout.addWidget(self.bt_saveCancelButtons)

    def handleSaveButton(self) -> None:
        """Save all options when save button was pressed."""
        logger.debug(f"handleSaveButton in {__class__.__name__}")

        emitUpdateSignal = False
        if (self.tab_general.hasUnsavedOptions()
                or self.tab_motors.hasUnsavedOptions()
                or self.tab_contactPoints.hasUnsavedOptions()
                or self.tab_solver.hasUnsavedOptions()):
            emitUpdateSignal = True

        self.tab_general.saveOptions()
        self.tab_motors.saveOptions()
        self.tab_contactPoints.saveOptions()
        self.tab_solver.saveOptions()

        if emitUpdateSignal:
            config.configRootUpdateDone.emit(self._configKey)
        self.close()

    # handle the close event for the log window
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event (QCloseEvent): The QCloseEvent.
        """
        logger.debug(f"closeEvent in {__class__.__name__}")

        # this might be removed later if it blocks processing data
        # check and warn for unsaved changes
        if (self.tab_general.hasUnsavedOptions()
                or self.tab_motors.hasUnsavedOptions()
                or self.tab_contactPoints.hasUnsavedOptions()
                or self.tab_solver.hasUnsavedOptions()):
            handleClosePrompt(self, event)


class TabGeneral(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the "general" tab with it's content."""
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey
        self.buildUi()
        # after UI is setup load options into ui elements
        self.loadOptsToGui(config, self._configKey)

    def buildUi(self) -> None:
        """Initialize UI elements."""
        # the tab's layout
        self.selfLayout = QFormLayout(self)

        # the group name
        self.le_groupName = QLineEdit(self)
        self.le_groupName.setMaxLength(35)
        self.addOpt("name", self.le_groupName)

        self.selfLayout.addRow("Group Name:", self.le_groupName)

    def hasUnsavedOptions(self) -> bool:
        """Check if this tab has unsaved options.

        Returns:
            bool: True if there are modified options otherwise False.
        """

        changedPaths = self.saveOptsFromGui(
            config, self._configKey, onlyDiff=True)
        return bool(changedPaths)

    def saveOptions(self) -> None:
        """Save the options from this tab."""

        self.saveOptsFromGui(config, self._configKey, blockSignal=True)


class TabMotors(QWidget):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the "motors" tab with it's content."""
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey + ".motors"
        self._data = deepcopy(config.get(self._configKey))

        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements."""
        # the tab's layout
        self.selfLayout = QVBoxLayout(self)

        # the table
        self.tv_motorsTable = QTableView(self)
        self.tv_motorsTable.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tv_motorsTable.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tv_motorsTable.setCornerButtonEnabled(False)
        self.tv_motorsTable.setSelectionMode(
            QTableView.SelectionMode.SingleSelection)
        cast(QHeaderView, self.tv_motorsTable.verticalHeader()
             ).setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        cast(QHeaderView, self.tv_motorsTable.verticalHeader()
             ).sectionClicked.connect(self.handleSelectionDelete)
        cast(QHeaderView, self.tv_motorsTable.horizontalHeader()
             ).setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cast(QHeaderView, self.tv_motorsTable.horizontalHeader()
             ).setSelectionMode(QHeaderView.SelectionMode.NoSelection)

        # Setup the table model
        self.motorsTableModel = SettingsTableModel(self._data)
        self.motorsTableModel.setHorizontalHeaderLabels(
            "Name", "ESP Id", "ESP Channel", "Min PWM", "Max PWM",
            "Radius", "X", "Y", "Z")
        self.motorsTableModel.setSettingsOrder(
            "name", "espAddr.0", "espAddr.1", "minPwm", "maxPwm",
            "r", "xyz.0", "xyz.1", "xyz.2")
        self.motorsTableModel.setSettingsDataTypes(
            str, int, int, int, int, float, float, float, float)

        # Assign the right delegate to the columns
        self.floatSpinBoxDelegate = FloatSpinBoxDelegate(4, -20.0, 20.0)
        self.pwmSpinBoxDelegate = IntSpinBoxDelegate(0, 255)
        self.espIdSpinBoxDelegate = IntSpinBoxDelegate(0, 20)
        for i, (t, n) in enumerate(zip(
                self.motorsTableModel.getSettingsDataTypes(),
                self.motorsTableModel.getSettingsOrder())):
            if t == float:
                self.tv_motorsTable.setItemDelegateForColumn(
                    i, self.floatSpinBoxDelegate)
            elif n in ("espAddr.0", "espAddr.1"):
                self.tv_motorsTable.setItemDelegateForColumn(
                    i, self.espIdSpinBoxDelegate)
            elif n in ("minPwm", "maxPwm"):
                self.tv_motorsTable.setItemDelegateForColumn(
                    i, self.pwmSpinBoxDelegate)

        self.tv_motorsTable.setModel(self.motorsTableModel)
        self.selfLayout.addWidget(self.tv_motorsTable)

        # the bar below the table
        self.hl_tabMotorsBelowTableBar = QHBoxLayout()

        # horizontal spacer
        self.spacer1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.hl_tabMotorsBelowTableBar.addItem(self.spacer1)

        # the add button
        self.pb_addMotor = QPushButton(self)
        self.pb_addMotor.setMaximumSize(QSize(40, 16777215))
        self.pb_addMotor.setText("\u2795")
        self.pb_addMotor.clicked.connect(self.handleAddButton)
        self.hl_tabMotorsBelowTableBar.addWidget(self.pb_addMotor)

        self.selfLayout.addLayout(self.hl_tabMotorsBelowTableBar)

    def handleSelectionDelete(self, index: int) -> None:
        col1 = self.motorsTableModel.data(
            self.motorsTableModel.index(index, 0),
            Qt.ItemDataRole.DisplayRole)
        promptResult = handleDeletePrompt(self, col1)
        if promptResult:
            self.motorsTableModel.removeRows(index, 1)

    def handleAddButton(self) -> None:
        self.motorsTableModel.insertRows(0)

    def hasUnsavedOptions(self) -> bool:
        """Check if this tab has unsaved options.

        Returns:
            bool: True if there are modified options otherwise False.
        """
        # only need to look at the table
        return self.motorsTableModel.settingsWereChanged

    def saveOptions(self) -> None:
        """Save the options from this tab."""
        config.set(self._configKey, self._data)
        self.motorsTableModel.settingsWereChanged = False


class TabContactPoints(QWidget):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the "Contact points" tab with it's content."""

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey + ".avatarPoints"
        self._data = deepcopy(config.get(self._configKey))

        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements."""
        # the tab's layout
        self.selfLayout = QVBoxLayout(self)

        # the table
        self.tv_contactPointsTable = QTableView(self)
        self.tv_contactPointsTable.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tv_contactPointsTable.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tv_contactPointsTable.setCornerButtonEnabled(False)
        self.tv_contactPointsTable.setSelectionMode(
            QTableView.SelectionMode.SingleSelection)
        cast(QHeaderView, self.tv_contactPointsTable.verticalHeader()
             ).setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        cast(QHeaderView, self.tv_contactPointsTable.verticalHeader()
             ).sectionClicked.connect(self.handleSelectionDelete)
        cast(QHeaderView, self.tv_contactPointsTable.horizontalHeader()
             ).setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cast(QHeaderView, self.tv_contactPointsTable.horizontalHeader()
             ).setSelectionMode(QHeaderView.SelectionMode.NoSelection)

        # Setup the table model
        self.contactPointsTableModel = SettingsTableModel(self._data)
        self.contactPointsTableModel.setHorizontalHeaderLabels(
            "Name", "ContactReceiver Name", "X", "Y", "Z", "Radius")
        self.contactPointsTableModel.setSettingsOrder(
            "name", "receiverId", "xyz.0", "xyz.1", "xyz.2", "r")
        self.contactPointsTableModel.setSettingsDataTypes(
            str, contactName, float, float, float, float)

        # Assign the right delegate to the columns
        self.floatSpinBoxDelegate = FloatSpinBoxDelegate(4, -20.0, 20.0)
        self.contactNameDelegate = LineEditMoreButtonDelegate()
        self.contactNameDelegate.buttonClicked.connect(
            self._handleContactNamePopupClick)
        for i, item in enumerate(self.contactPointsTableModel
                                 .getSettingsDataTypes()):
            if item == float:
                self.tv_contactPointsTable.setItemDelegateForColumn(
                    i, self.floatSpinBoxDelegate)
            elif item == contactName:
                self.tv_contactPointsTable.setItemDelegateForColumn(
                    i, self.contactNameDelegate)

        self.tv_contactPointsTable.setModel(self.contactPointsTableModel)
        self.selfLayout.addWidget(self.tv_contactPointsTable)

        # the bar below the table
        self.hl_tabContactPointsBelowTableBar = QHBoxLayout()

        # horizontal spacer
        self.spacer1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.hl_tabContactPointsBelowTableBar.addItem(self.spacer1)

        # the add button
        self.pb_addContactPoint = QPushButton(self)
        self.pb_addContactPoint.setMaximumSize(QSize(40, 16777215))
        self.pb_addContactPoint.setText("\u2795")
        self.pb_addContactPoint.clicked.connect(self.handleAddButton)
        self.hl_tabContactPointsBelowTableBar.addWidget(
            self.pb_addContactPoint)

        self.selfLayout.addLayout(self.hl_tabContactPointsBelowTableBar)

    def _handleContactNamePopupClick(self, index: int) -> None:
        self.selWin = VrcContactReceiverNameSelectionWindow(index)
        self.selWin.selectedOption.connect(self._handleContactNamePopupInsert)
        self.selWin.show()

    def _handleContactNamePopupInsert(self, rowId: int, name: str) -> None:
        self.contactPointsTableModel.setData(
            self.contactPointsTableModel.index(rowId, 1), name)
        if hasattr(self, "selWin") and self.selWin:
            self.selWin.close()
        self.selWin = None

    def handleSelectionDelete(self, index: int) -> None:
        col1 = self.contactPointsTableModel.data(
            self.contactPointsTableModel.index(index, 0),
            Qt.ItemDataRole.DisplayRole)
        promptResult = handleDeletePrompt(self, col1)
        if promptResult:
            self.contactPointsTableModel.removeRows(index, 1)

    def handleAddButton(self) -> None:
        self.contactPointsTableModel.insertRows(0)

    def hasUnsavedOptions(self) -> bool:
        """Check if this tab has unsaved options.

        Returns:
            bool: True if there are modified options otherwise False.
        """
        # only need to look at the table
        return self.contactPointsTableModel.settingsWereChanged

    def saveOptions(self) -> None:
        """Save the options from this tab."""
        config.set(self._configKey, self._data)
        self.contactPointsTableModel.settingsWereChanged = False


class TabSolver(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the "solver" tab with it's content."""
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey + ".solver"
        self.buildUi()
        # after UI is setup load options into ui elements
        self.loadOptsToGui(config, self._configKey)
        # update ui-element visibility
        self.changeSolver(config.get(f"{self._configKey}.solverType"))

    def buildUi(self) -> None:
        """Initialize UI elements."""
        # the tab's layout
        self.selfLayout = QFormLayout(self)

        # the solver name
        self.cb_solverType = QComboBox(self)
        for type in SolverType:
            self.cb_solverType.addItem(type)
        self.cb_solverType.currentTextChanged.connect(self.changeSolver)
        self.addOpt("solverType", self.cb_solverType)
        self.selfLayout.addRow("Solver Type:", self.cb_solverType)

        # a dividing line
        self.ln_spacer = QFrame()
        self.ln_spacer.setFrameShape(QFrame.Shape.HLine)
        self.ln_spacer.setFrameShadow(QFrame.Shadow.Raised)
        self.selfLayout.addRow(self.ln_spacer)

    def changeSolver(self, selected: str) -> None:
        """Changes out the settings for each solver type.

        Args:
            selected (str): The selected solver.
        """
        if hasattr(self, "solverSettingsWidget") and self.solverSettingsWidget:
            self.solverSettingsWidget.deleteLater()
            self.selfLayout.removeRow(self.solverSettingsWidget)
            self.solverSettingsWidget = None
        settingsWidget = SolverSettingsFactory.fromType(SolverType(selected))
        if settingsWidget:
            self.solverSettingsWidget = settingsWidget(self._configKey)
            self.selfLayout.addRow(self.solverSettingsWidget)

    def hasUnsavedOptions(self) -> bool:
        """Check if this tab has unsaved options.

        Returns:
            bool: True if there are modified options otherwise False.
        """
        changedPaths = self.saveOptsFromGui(
            config, self._configKey, onlyDiff=True)
        changedSolverSettings = []
        if hasattr(self, "solverSettingsWidget") and self.solverSettingsWidget:
            changedSolverSettings = self.solverSettingsWidget.hasUnsavedOptions()
        return bool(changedPaths) or bool(changedSolverSettings)

    def saveOptions(self) -> None:
        """Save the options from this tab."""
        if hasattr(self, "solverSettingsWidget") and self.solverSettingsWidget:
            self.solverSettingsWidget.saveOptions()
        self.saveOptsFromGui(config, self._configKey, blockSignal=True)


class BaseSolverSettingsRow(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the settings widget for a solver"""
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey
        self.selfLayout = QFormLayout(self)
        self.buildUi()
        self.loadOptsToGui(config, self._configKey)

    def buildUi(self) -> None:
        raise NotImplementedError

    def hasUnsavedOptions(self) -> bool:
        """Check if this tab has unsaved options.

        Returns:
            bool: True if there are modified options otherwise False.
        """
        changedPaths = self.saveOptsFromGui(
            config, self._configKey, onlyDiff=True)
        return bool(changedPaths)

    def saveOptions(self) -> None:
        """Save the options from this tab."""
        self.saveOptsFromGui(config, self._configKey, blockSignal=True)


class MLATSolverSettings(BaseSolverSettingsRow):
    def buildUi(self):
        # the strength spinbox
        self.sb_strength = QSpinBox(self)
        self.sb_strength.setMinimum(0)
        self.sb_strength.setMaximum(100)
        self.sb_strength.setSuffix(" %")
        self.addOpt("strength", self.sb_strength, int)
        self.selfLayout.addRow("Strength", self.sb_strength)

        # upper sphere check
        self.cb_allowOnlyUpperSphereHalf = QCheckBox(self)
        self.cb_allowOnlyUpperSphereHalf.setText(
            "Only allow upper sphere half")
        self.addOpt("MLAT_enableHalfSphereCheck",
                    self.cb_allowOnlyUpperSphereHalf, bool)
        self.selfLayout.addRow("", self.cb_allowOnlyUpperSphereHalf)

        # contact only (on/off instead of pwm, might be better in the contact point?)
        self.cb_contactOnly = QCheckBox(self)
        self.cb_contactOnly.setText("Contact only")
        self.addOpt("contactOnly", self.cb_contactOnly, bool)
        self.selfLayout.addRow("", self.cb_contactOnly)


class SINGLEN2NSolverSettings(BaseSolverSettingsRow):
    def buildUi(self):
        # the strength spinbox
        self.sb_strength = QSpinBox(self)
        self.sb_strength.setMinimum(0)
        self.sb_strength.setMaximum(100)
        self.sb_strength.setSuffix(" %")
        self.addOpt("strength", self.sb_strength, int)
        self.selfLayout.addRow("Strength", self.sb_strength)

        # min max setting
        self.cb_minmax = QComboBox(self)
        self.cb_minmax.addItems(["Min", "Max", "Mean"])
        self.addOpt("SINGLEN2N_mode", self.cb_minmax)
        self.selfLayout.addRow("Mode:", self.cb_minmax)

        # contact only (on/off instead of pwm, might be better in the contact point?)
        self.cb_contactOnly = QCheckBox(self)
        self.cb_contactOnly.setText("Contact only")
        self.addOpt("contactOnly", self.cb_contactOnly, bool)
        self.selfLayout.addRow("", self.cb_contactOnly)


class SolverSettingsFactory:
    @staticmethod
    def fromType(solverType: SolverType) -> \
            type[MLATSolverSettings] | \
            type[SINGLEN2NSolverSettings] | None:
        match solverType:
            case SolverType.MLAT:
                return MLATSolverSettings
            case SolverType.SINGLEN2N:
                return SINGLEN2NSolverSettings


class contactName(str):
    pass


type validValueTypes = type[str] | type[int] | type[float] \
    | type[bool] | type[list] | type[dict] | type[contactName]


class SettingsTableModel(QAbstractTableModel):
    """A table model for handling settings.

    Attributes:
        settingsWereChanged (bool): Flag for tracking changes in settings.
        _data: The data for the table.
        _headerLabels (list): The labels for the table headers.
        _settingsOrder (list): The order of the settings.
        _settingsDataTypes (list): The data types for the settings.
    """

    def __init__(self, data: dict) -> None:
        """Initializes the ContactPointSettingsTableModel.

        Args:
            data (dict): The data for the table.
        """
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__()
        self.settingsWereChanged = False
        self._data = data
        self._headerLabels: tuple
        self._settingsOrder: tuple
        self._settingsDataTypes: tuple

    def setHorizontalHeaderLabels(self, *headerLabels: str) -> None:
        self._headerLabels = headerLabels

    def setSettingsOrder(self, *settingsOrder: str) -> None:
        self._settingsOrder = settingsOrder

    def getSettingsOrder(self) -> tuple:
        return self._settingsOrder

    def setSettingsDataTypes(self, *settingsDataTypes) -> None:
        self._settingsDataTypes = settingsDataTypes

    def getSettingsDataTypes(self) -> tuple:
        return self._settingsDataTypes

    def data(self, index: QModelIndex, role: int) -> Any:
        """Gets the current data for each cell.

        Args:
            index (QModelIndex): The index of the cell.
            role (int): The action role.

        Returns:
            Any: The data for the cell or QVariant if index is invalid
        """
        if not index.isValid():
            return QVariant()

        if role in (Qt.ItemDataRole.DisplayRole,
                    Qt.ItemDataRole.EditRole):
            data = self._getRowColConfigVal(index)
            if isinstance(data, contactName):
                # special handling for contactName type
                return str(data)
            return data

    def setData(self, index: QModelIndex, value: Any,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
        """Sets new data for each cell.

        Args:
            index (QModelIndex): The index of the cell.
            value (Any): The new value for the cell.
            role (int, optional): The action role. Defaults to
                Qt.ItemDataRole.EditRole.

        Returns:
            bool: True if the data was set successfully,
                False otherwise.
        """
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            logger.debug(f"EditRole: {role} Row: {index.row()} "
                         f"Col: {index.column()} Value: {value}")
            dataType = self._getDataTypeForCol(index)
            # Don't allow empty values
            if value == "":
                return False
            # check if supplied data is right type
            try:
                newValue = dataType(value)
            except (TypeError, ValueError):
                return False
            self._setRowColConfigVal(index, newValue)
            self.dataChanged.emit(index, index)
        return True

    def removeRows(self, row: int, count: int = 1,
                   parent: QModelIndex = QModelIndex()) -> bool:
        """Removes rows from the table.

        Args:
            row (int): The row to remove.
            count (int, optional): The number of rows to remove.
                Defaults to 1.
            parent (QModelIndex, optional): The parent index. Defaults
                to QModelIndex(). Unused because Table

        Returns:
            bool: False if the last entry is being removed,
                True otherwise.
        """
        # don't allow removing the last entry
        if self.rowCount() <= 1:
            return False
        self.beginRemoveRows(parent, row, row+count-1)
        PathReader.delOption(self._data, str(row))
        self.settingsWereChanged = True
        self.endRemoveRows()
        return False

    def insertRows(self, row: int, count: int = 1,
                   parent: QModelIndex = QModelIndex()) -> bool:
        """Inserts rows into the table.

        Args:
            row (int): The row to insert at.
            count (int, optional): The number of rows to insert.
                Defaults to 1.
            parent (QModelIndex, optional): The parent index. Defaults to
                QModelIndex().

        Returns:
            bool: Always true.
        """
        self.beginInsertRows(parent, self.rowCount(), self.rowCount()+count-1)
        PathReader.setOption(
            self._data, str(self.rowCount()), deepcopy(
                self._data[self.rowCount()-1]),
            inPlace=True)
        self.endInsertRows()
        self.settingsWereChanged = True
        return True

    def _getRowColConfigVal(self, index: QModelIndex) -> Any:
        """Return the current configuration for a given cell."""
        return PathReader.getOption(
            self._data[index.row()], self._colToKey(index))

    def _setRowColConfigVal(self, index: QModelIndex, newValue) -> Any:
        """Update the option with a new value based on the given cell."""

        path = f"{index.row()}.{self._colToKey(index)}"
        PathReader.setOption(self._data, path, newValue, inPlace=True)
        self.settingsWereChanged = True

    def _getDataTypeForCol(self, index: QModelIndex) -> validValueTypes:
        """Return the data type required for the given cell."""
        return self._settingsDataTypes[index.column()]

    def _colToKey(self, index: QModelIndex) -> str:
        """Map a column id to the required configuration key."""
        return self._settingsOrder[index.column()]

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the row count required for the table."""
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the column count required for the table"""

        return len(self._settingsOrder)

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int) -> str | None:
        """Handle returning the header label based on the given index."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and self._headerLabels:
                return self._headerLabels[section]
            elif orientation == Qt.Orientation.Vertical:
                return "\U0001F5D1"  # Yes it's the trash bin icon

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Add ItemIsEditable flag to the cell."""
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable


class VrcContactReceiverNameSelectionWindow(QWidget):
    selectedOption = QSignal(int, str)

    def __init__(self, rowId: int, *args, **kwargs) -> None:
        """Initialize contact name selection window."""

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._avatars = getVrcAvatars()
        self._rowId = rowId
        self.buildUi()
        self._loadAvatarOptions()

    def buildUi(self) -> None:
        """Initialize UI elements."""
        self.setWindowTitle("Contact Receiver Selection")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(439, 115)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        self.selfLayout = QFormLayout(self)
        self.cb_avatar = QComboBox(self)
        self.cb_avatar.setMaxVisibleItems(20)
        self.cb_avatar.currentTextChanged.connect(
            self._avatarSelectionChanged)
        self.selfLayout.addRow("Avatar", self.cb_avatar)

        self.cb_parameter = QComboBox(self)
        self.cb_parameter.setMaxVisibleItems(20)
        self.selfLayout.addRow("Parameter", self.cb_parameter)

        self.pb_insertName = QPushButton(self)
        self.pb_insertName.setText(random.choice(
            ["Use this Contact Parameter", "UwU!"]))
        self.pb_insertName.setToolTip(
            "Select this Contact Parameter")
        self.pb_insertName.clicked.connect(self._saveAndClose)
        self.selfLayout.addRow(self.pb_insertName)

    def _loadAvatarOptions(self) -> None:
        self.cb_avatar.addItems([avatar.name for avatar in self._avatars])

    def _avatarSelectionChanged(self, name: str) -> None:
        self.cb_parameter.clear()
        self.cb_parameter.addItems(self._getAvatarContactNames(name))

    def _getAvatarContactNames(self, name: str) -> list:
        avatars = (avatar for avatar in self._avatars if avatar.name == name)
        selected = next(avatars, None)
        if selected:
            return [param["address"][19:] for param
                    in selected.outputParameters
                    if param["address"][19:] not in vrcInternals]
        return []

    def _saveAndClose(self):
        self.selectedOption.emit(self._rowId,
                                 self.cb_parameter.currentText())


if __name__ == "__main__":
    print("There is no point running this file directly")
