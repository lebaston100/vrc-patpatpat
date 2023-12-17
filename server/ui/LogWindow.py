from logging import Logger

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QComboBox, QHBoxLayout, QPlainTextEdit,
                             QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget)

from modules import config
from utils import LoggerClass, SignalLogHandler

logger = LoggerClass.getSubLogger(__name__)


class LogWindow(QWidget):
    """A widget without a parent (aka a new window) to display logging
    events at a configurable logging level.
    """

    def __init__(self, logger: Logger, initialLogLevel: str = "DEBUG",
                 *args, **kwargs) -> None:
        """Initialize window that display the logger output.

        Args:
            logger (Logger): The Logger we want to listen to.
        """

        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)
        self._logWindowHandler = SignalLogHandler()
        self._initialLogLevel = initialLogLevel
        self._logWindowHandler.changeLevel(self._initialLogLevel)
        self._rootLogger = logger
        # only attach the handler while the window is alive
        self._rootLogger.addHandler(self._logWindowHandler)
        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements.
        """

        # the widget and it's layout
        self.setWindowTitle("Log Window")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(1380, 650)
        self.LogWindowWidgetLayout = QVBoxLayout(self)
        self.LogWindowWidgetLayout.setObjectName("LogWindowWidgetLayout")

        # log textbox
        self.te_logView = QPlainTextEdit(self)
        self.te_logView.setObjectName("te_logView")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.te_logView.setSizePolicy(sizePolicy)
        self.te_logView.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.te_logView.setUndoRedoEnabled(False)
        self.te_logView.setReadOnly(True)

        self.LogWindowWidgetLayout.addWidget(self.te_logView)

        # the footer row with the usable ui elements
        self.footerRowLayout = QHBoxLayout()
        self.footerRowLayout.setObjectName("footerRowLayout")

        # spacer to push buttons to the right
        self.spacer1 = QSpacerItem(40, 20,
                                   QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Minimum)
        self.footerRowLayout.addItem(self.spacer1)

        # the log level selection dropdown
        self.cb_logLevel = QComboBox(self)
        for level in LoggerClass.getLoggingLevelStrings():
            self.cb_logLevel.addItem(level)
        self.cb_logLevel.setCurrentText(self._initialLogLevel)
        self.cb_logLevel.setObjectName("cb_logLevel")
        self.footerRowLayout.addWidget(self.cb_logLevel)

        # the clear log button
        self.pb_clearLog = QPushButton(self)
        self.pb_clearLog.setObjectName("pb_clearLog")
        self.pb_clearLog.setText("Clear Log")
        self.footerRowLayout.addWidget(self.pb_clearLog)

        self.LogWindowWidgetLayout.addLayout(self.footerRowLayout)

        # connect signals
        self.pb_clearLog.clicked.connect(self.te_logView.clear)
        self.cb_logLevel.currentTextChanged.connect(
            self._logWindowHandler.changeLevel)
        self._logWindowHandler.signal.newLogEntry.connect(
            self.te_logView.appendHtml)

    # handle the close event for the log window
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Remove log handler from logger.

        Args:
            event (QCloseEvent  |  None]): The qt event.

        Returns:
            None
        """

        logger.debug(f"closeEvent in {__class__.__name__}")
        self._rootLogger.removeHandler(self._logWindowHandler)


if __name__ == "__main__":
    logger.error("There is no point running this file directly")
