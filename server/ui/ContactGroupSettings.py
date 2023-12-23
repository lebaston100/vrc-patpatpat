"""The contact group settings window
"""

from copy import deepcopy
from typing import Any, cast

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QSize, Qt
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QCheckBox,
                             QComboBox, QDialogButtonBox, QFormLayout,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                             QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
                             QTableView, QTabWidget, QVBoxLayout, QWidget)

from modules import OptionAdapter, config
from ui.uiHelpers import handleClosePrompt, handleDeletePrompt
from utils import LoggerClass, PathReader

logger = LoggerClass.getSubLogger(__name__)


class ContactGroupSettings(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Initialize contact settings window
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = "groups.group" + configKey

        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements.
        All of the tabs are in their own subclass.
        """

        # the widget and it's layout
        self.setWindowTitle("Contact Group Settings")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(980, 500)
        self.selfLayout = QVBoxLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # the tab widget
        self.mainTabWidget = QTabWidget(self)
        self.mainTabWidget.setObjectName("mainTabWidget")

        # add all 4 tabs to the tab widget
        self.tab_general = TabGeneral(self._configKey)
        self.mainTabWidget.addTab(self.tab_general, "General")

        self.tab_motors = TabMotors(self._configKey)
        self.mainTabWidget.addTab(self.tab_motors, "Motors")

        self.tab_colliderPoints = TabColliderPoints(self._configKey)
        self.mainTabWidget.addTab(self.tab_colliderPoints, "Collider Points")

        self.tab_solver = TabSolver(self._configKey)
        self.mainTabWidget.addTab(self.tab_solver, "Solver")

        self.mainTabWidget.setCurrentIndex(0)
        self.selfLayout.addWidget(self.mainTabWidget)

        # save/cancel buttons
        self.bt_saveCancelButtons = QDialogButtonBox(self)
        self.bt_saveCancelButtons.setObjectName("bt_saveCancelButtons")
        self.bt_saveCancelButtons.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save)
        self.bt_saveCancelButtons.rejected.connect(self.close)
        self.bt_saveCancelButtons.accepted.connect(self.handleSaveButton)

        self.selfLayout.addWidget(self.bt_saveCancelButtons)

    def handleSaveButton(self) -> None:
        """Save all options when save button was pressed
        """

        logger.debug(f"handleSaveButton in {__class__.__name__}")
        # TODO: Save other tabs too
        self.tab_general.saveOptions()
        self.tab_colliderPoints.saveOptions()
        self.tab_solver.saveOptions()
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
        # TODO: Check other tabs too
        if (self.tab_general.hasUnsavedOptions()
                or self.tab_solver.hasUnsavedOptions()
                or self.tab_colliderPoints.hasUnsavedOptions()):
            handleClosePrompt(self, event)


class TabGeneral(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the "general" tab with it's content
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey
        self.buildUi()
        # after UI is setup load options into ui elements
        self.loadOptsToGui(config, self._configKey)

    def buildUi(self) -> None:
        """Initialize UI elements.
        """

        # the tab's layout
        self.selfLayout = QFormLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # the group name
        self.le_groupName = QLineEdit(self)
        self.le_groupName.setObjectName("le_groupName")
        self.le_groupName.setMaxLength(35)
        self.addOpt("name", self.le_groupName)

        self.selfLayout.addRow("Group Name:", self.le_groupName)

    def hasUnsavedOptions(self) -> bool:
        """Check if this tab has unsaved options.

        Returns:
            bool: True if there are modified options otherwise False.
        """

        changedPaths = self.saveOptsFromGui(config, self._configKey, True)
        return bool(changedPaths)

    def saveOptions(self) -> None:
        """Save the options from this tab.
        """

        self.saveOptsFromGui(config, self._configKey)


class TabMotors(QWidget):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the "motors" tab with it's content
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey + ".motors"

        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements.
        """

        # the tab's layout
        self.selfLayout = QVBoxLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # the table
        self.tv_motorsTable = QTableView(self)
        self.tv_motorsTable.setObjectName("tv_motorsTable")
        self.tv_motorsTable.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tv_motorsTable.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tv_motorsTable.setCornerButtonEnabled(False)
        # self.tv_motorsTable.verticalHeader().setVisible(True)

        # TODO: we need a table model
        # self.tv_motorsTable.setModel()

        self.selfLayout.addWidget(self.tv_motorsTable)

        # the bar below the table
        self.hl_tabMotorsBelowTableBar = QHBoxLayout()
        self.hl_tabMotorsBelowTableBar.setObjectName(
            "hl_tabMotorsBelowTableBar")

        # horizontal spacer
        self.spacer1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.hl_tabMotorsBelowTableBar.addItem(self.spacer1)

        # the remove and add button
        self.pb_removeMotor = QPushButton(self)
        self.pb_removeMotor.setObjectName("pb_removeMotor")
        self.pb_removeMotor.setMaximumSize(QSize(40, 16777215))
        self.pb_removeMotor.setText("\u2795")
        self.hl_tabMotorsBelowTableBar.addWidget(self.pb_removeMotor)

        self.pb_addMotor = QPushButton(self)
        self.pb_addMotor.setObjectName("pb_addMotor")
        self.pb_addMotor.setMaximumSize(QSize(40, 16777215))
        self.pb_addMotor.setText("\u2796")
        self.hl_tabMotorsBelowTableBar.addWidget(self.pb_addMotor)

        self.selfLayout.addLayout(self.hl_tabMotorsBelowTableBar)


class TabColliderPoints(QWidget):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the "collider points" tab with it's content
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._configKey = configKey + ".avatarPoints"
        self._data = deepcopy(config.get(self._configKey))

        self.buildUi()

        # TODO: Add custom QItemDelegate for the view (float fields)

    def buildUi(self) -> None:
        """Initialize UI elements.
        """

        # the tab's layout
        self.selfLayout = QVBoxLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # the table
        self.tv_colliderPointsTable = QTableView(self)
        self.tv_colliderPointsTable.setObjectName("tv_colliderPointsTable")
        self.tv_colliderPointsTable.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tv_colliderPointsTable.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tv_colliderPointsTable.setCornerButtonEnabled(False)
        self.tv_colliderPointsTable.setSelectionMode(
            QTableView.SelectionMode.SingleSelection)
        cast(QHeaderView, self.tv_colliderPointsTable.verticalHeader()
             ).setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        cast(QHeaderView, self.tv_colliderPointsTable.verticalHeader()
             ).sectionClicked.connect(self.handleSelectionDelete)
        cast(QHeaderView, self.tv_colliderPointsTable.horizontalHeader()
             ).setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cast(QHeaderView, self.tv_colliderPointsTable.horizontalHeader()
             ).setSelectionMode(QHeaderView.SelectionMode.NoSelection)

        self.colliderPointsTableModel = ColliderPointSettingsTableModel(
            self._data)
        self.tv_colliderPointsTable.setModel(self.colliderPointsTableModel)

        self.selfLayout.addWidget(self.tv_colliderPointsTable)

        # the bar below the table
        self.hl_tabColliderPointsBelowTableBar = QHBoxLayout()
        self.hl_tabColliderPointsBelowTableBar.setObjectName(
            "hl_tabMotorsBelowTableBar")

        # horizontal spacer
        self.spacer1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.hl_tabColliderPointsBelowTableBar.addItem(self.spacer1)

        # the add button
        self.pb_removeColliderPoint = QPushButton(self)
        self.pb_removeColliderPoint.setObjectName("pb_removeColliderPoint")
        self.pb_removeColliderPoint.setMaximumSize(QSize(40, 16777215))
        self.pb_removeColliderPoint.setText("\u2795")
        self.pb_removeColliderPoint.clicked.connect(self.handleAddButton)
        self.hl_tabColliderPointsBelowTableBar.addWidget(
            self.pb_removeColliderPoint)

        self.selfLayout.addLayout(self.hl_tabColliderPointsBelowTableBar)

    def handleSelectionDelete(self, index: int) -> None:
        col1 = self.colliderPointsTableModel.data(
            self.colliderPointsTableModel.index(index, 0),
            Qt.ItemDataRole.UserRole)
        promptResult = handleDeletePrompt(self, col1)
        if promptResult:
            self.colliderPointsTableModel.removeRows(index, 1)

    def handleAddButton(self) -> None:
        self.colliderPointsTableModel.insertRows(0)

    def hasUnsavedOptions(self) -> bool:
        """Check if this tab has unsaved options.

        Returns:
            bool: True if there are modified options otherwise False.
        """

        # only need to look at the table
        return self.colliderPointsTableModel.settingsWereChanged

    def saveOptions(self) -> None:
        """Save the options from this tab.
        """

        config.set(self._configKey, self._data)
        self.colliderPointsTableModel.settingsWereChanged = False


class TabSolver(QWidget, OptionAdapter):
    def __init__(self, configKey: str, *args, **kwargs) -> None:
        """Create the "solver" tab with it's content
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self._currentSolver = ""
        self._solverOptionMapping = []

        self._configKey = configKey + ".solver"
        self.buildUi()
        # after UI is setup load options into ui elements
        self.loadOptsToGui(config, self._configKey)
        # update ui-element visibility
        self.changeSolver(config.get(f"{self._configKey}.solverType"))

    def buildUi(self) -> None:
        """Initialize UI elements.
        """

        # the tab's layout
        self.selfLayout = QFormLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # the solver name
        self.cb_solverType = QComboBox(self)
        self.cb_solverType.addItem("Mlat")
        self.cb_solverType.addItem("SimpleDistance")
        self.cb_solverType.setObjectName("cb_solverType")
        self.cb_solverType.setCurrentText("Mlat")
        self.cb_solverType.currentTextChanged.connect(self.changeSolver)
        self.addOpt("solverType", self.cb_solverType)

        self.selfLayout.addRow("Solver Type:", self.cb_solverType)

        # upper sphere check
        self.cb_allowOnlyUpperSphereHalf = QCheckBox(self)
        self.cb_allowOnlyUpperSphereHalf.setObjectName(
            "cb_allowOnlyUpperSphereHalf")
        self.cb_allowOnlyUpperSphereHalf.setText(
            "Only allow upper sphere half")
        self.addOpt("enableHalfSphereCheck",
                    self.cb_allowOnlyUpperSphereHalf, bool)
        self._solverOptionMapping.append(
            ("Mlat", self.cb_allowOnlyUpperSphereHalf))

        self.selfLayout.addRow("", self.cb_allowOnlyUpperSphereHalf)

        # contact only (on/off instead of pwm, might be better in the contact point?)
        self.cb_contactOnly = QCheckBox(self)
        self.cb_contactOnly.setObjectName("cb_contactOnly")
        self.cb_contactOnly.setText("Contact only")
        self.addOpt("contactOnly", self.cb_contactOnly, bool)

        self.selfLayout.addRow("", self.cb_contactOnly)

        # spacer
        self.spacer1 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.selfLayout.addItem(self.spacer1)

    def changeSolver(self, selected: str) -> None:
        self._currentSolver = selected
        for solver, uiElement in self._solverOptionMapping:
            if solver == self._currentSolver:
                uiElement.show()
            else:
                uiElement.hide()

    def hasUnsavedOptions(self) -> bool:
        """Check if this tab has unsaved options.

        Returns:
            bool: True if there are modified options otherwise False.
        """

        changedPaths = self.saveOptsFromGui(config, self._configKey, True)
        return bool(changedPaths)

    def saveOptions(self) -> None:
        """Save the options from this tab.
        """

        self.saveOptsFromGui(config, self._configKey)


type validValueTypes = type[str] | type[int] | type[float] \
    | type[bool] | type[list] | type[dict]


# maybe we can re-use this for the motors table?
# don't see why not, can just make the few things configurable in init
class ColliderPointSettingsTableModel(QAbstractTableModel):
    """A table model for handling collider point settings.

    Attributes:
        settingsWereChanged (bool): Flag for tracking changes in settings.
        _data: The data for the table.
        _headerLabels (list): The labels for the table headers.
        _settingsOrder (list): The order of the settings.
        _settingsDataTypes (list): The data types for the settings.
    """

    def __init__(self, data: dict) -> None:
        """Initializes the ColliderPointSettingsTableModel.

        Args:
            data (dict): The data for the table.
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__()
        self.settingsWereChanged = False

        self._data = data
        self._headerLabels = [
            "Name", "ContactReceiver Name", "X", "Y", "Z", "Radius"]
        self._settingsOrder = ["name", "receiverId",
                               "xyz.0", "xyz.1", "xyz.2", "r"]
        self._settingsDataTypes = [str, str, float, float, float, float]

    def data(self, index: QModelIndex, role: int) -> Any:
        """Gets the current data for each cell.

        Args:
            index (QModelIndex): The index of the cell.
            role (int): The action role.

        Returns:
            Any: The data for the cell.
        """

        if role in (Qt.ItemDataRole.DisplayRole,
                    Qt.ItemDataRole.EditRole,
                    Qt.ItemDataRole.UserRole):
            return str(self._getRowColConfigVal(index))

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
            if not value:
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
        """Return the current configuration for a given cell
        """

        return PathReader.getOption(
            self._data[index.row()], self._colToKey(index))

    def _setRowColConfigVal(self, index: QModelIndex, newValue) -> Any:
        """Update the option with a new value based on the given cell
        """

        path = f"{index.row()}.{self._colToKey(index)}"
        PathReader.setOption(self._data, path, newValue, inPlace=True)
        self.settingsWereChanged = True

    def _getDataTypeForCol(self, index: QModelIndex) -> validValueTypes:
        """Return the data type required for the given cell
        """

        return self._settingsDataTypes[index.column()]

    def _colToKey(self, index: QModelIndex) -> str:
        """Map a column id to the required configuration key
        """

        return self._settingsOrder[index.column()]

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the row count required for the table
        """

        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the column count required for the table
        """

        return len(self._settingsOrder)

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int) -> str | None:
        """Handle returning the header label based on the given index
        """

        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headerLabels[section]
            elif orientation == Qt.Orientation.Vertical:
                return "\U0001F5D1"  # Yes it's the trash bin icon

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Add ItemIsEditable flag to the cell
        """

        return super().flags(index) | Qt.ItemFlag.ItemIsEditable


if __name__ == "__main__":
    print("There is no point running this file directly")
