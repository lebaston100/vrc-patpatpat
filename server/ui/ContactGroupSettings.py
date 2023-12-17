"""The contact group settings window
"""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QComboBox,
                             QDialogButtonBox, QFormLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QSizePolicy,
                             QSpacerItem, QSpinBox, QTableView, QTabWidget,
                             QVBoxLayout, QWidget)

from modules import OptionAdapter, config
from ui.uiHelpers import handleCloseEvent
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class ContactGroupSettings(QWidget, OptionAdapter):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize contact settings window
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.buildUi()
        self._configKey = "TBD"

        # TODO: There are a lot of ui elements in here
        # also special ones we need a custom way in the ui reader/writer
        # to write and read from views.

        # after UI is setup load options into ui elements
        # self.loadOptsToGui(config.get(self._configKey))

    def buildUi(self):
        """Initialize UI elements.
        All of the tabs are in their own subclass.
        """

        # the widget and it's layout
        self.setWindowTitle("Contact Group Settings")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(850, 500)
        self.selfLayout = QVBoxLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # the tab widget
        self.mainTabWidget = QTabWidget(self)
        self.mainTabWidget.setObjectName("mainTabWidget")

        # add all 4 tabs to the tab widget
        self.tab_general = TabGeneral()
        self.mainTabWidget.addTab(self.tab_general, "General")

        self.tab_motors = TabMotors()
        self.mainTabWidget.addTab(self.tab_motors, "Motors")

        self.tab_colliderPoints = TabColliderPoints()
        self.mainTabWidget.addTab(self.tab_colliderPoints, "Collider Points")

        self.tab_solver = TabSolver()
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


class TabGeneral(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        """Create the "general" tab with it's content
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.buildUi()

    def buildUi(self):
        """Initialize UI elements.
        """

        # the tab's layout
        self.selfLayout = QFormLayout(self)
        self.selfLayout.setObjectName("selfLayout")

        # the group name
        self.le_groupName = QLineEdit(self)
        self.le_groupName.setObjectName("le_groupName")
        self.le_groupName.setMaxLength(35)

        self.selfLayout.addRow("Group Name:", self.le_groupName)


class TabMotors(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        """Create the "motors" tab with it's content
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.buildUi()

    def buildUi(self):
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
    def __init__(self, *args, **kwargs) -> None:
        """Create the "collider points" tab with it's content
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.buildUi()

    def buildUi(self):
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
        # self.tv_colliderPointsTable.verticalHeader().setVisible(True)

        # TODO: we need a table model
        # self.tv_colliderPointsTable.setModel()

        self.selfLayout.addWidget(self.tv_colliderPointsTable)

        # the bar below the table
        self.hl_tabColliderPointsBelowTableBar = QHBoxLayout()
        self.hl_tabColliderPointsBelowTableBar.setObjectName(
            "hl_tabMotorsBelowTableBar")

        # horizontal spacer
        self.spacer1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.hl_tabColliderPointsBelowTableBar.addItem(self.spacer1)

        # the remove and add button
        self.pb_removeColliderPoint = QPushButton(self)
        self.pb_removeColliderPoint.setObjectName("pb_removeColliderPoint")
        self.pb_removeColliderPoint.setMaximumSize(QSize(40, 16777215))
        self.pb_removeColliderPoint.setText("\u2795")
        self.hl_tabColliderPointsBelowTableBar.addWidget(
            self.pb_removeColliderPoint)

        self.pb_addColliderPoint = QPushButton(self)
        self.pb_addColliderPoint.setObjectName("pb_addColliderPoint")
        self.pb_addColliderPoint.setMaximumSize(QSize(40, 16777215))
        self.pb_addColliderPoint.setText("\u2796")
        self.hl_tabColliderPointsBelowTableBar.addWidget(
            self.pb_addColliderPoint)

        self.selfLayout.addLayout(self.hl_tabColliderPointsBelowTableBar)


class TabSolver(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        """Create the "solver" tab with it's content
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        # This keeps track of the current visible solver to we know
        # if we need to swap out the selection
        self.currentSolver = ""

        self.buildUi()

    def buildUi(self):
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
        # or textActivated, well see

        self.selfLayout.addRow("Solver Type:", self.cb_solverType)

        # assemble the solvers settings here, either as it's own class
        # or just a function. i like class more, maybe add a line below
        # on

        # spacer
        self.spacer1 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.selfLayout.addItem(self.spacer1)

    def changeSolver(self, selected: str):
        # change which solver options are shown here
        self.currentSolver = selected
        pass

    def getMlatSolverSettings(self):
        pass


if __name__ == "__main__":
    print("There is no point running this file directly")
