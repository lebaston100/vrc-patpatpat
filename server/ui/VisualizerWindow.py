from PyQt6.QtCore import Qt
from PyQt6.QtDataVisualization import Q3DScatter
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSlider,
                             QVBoxLayout, QWidget)

from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class VisualizerWindow(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize the 3d visualizer window"""
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)

        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements."""
        self.setWindowTitle("3D Visualizer for TODO")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(500, 500)

        self.selfLayout = QVBoxLayout(self)
        self.buttonRowLayout = QHBoxLayout()

        self.visualizer = Visualizer()
        self.selfLayout.addWidget(self.visualizer)

        self.bt_clearPlot = QPushButton("Clear Plot")
        self.bt_clearPlot.clicked.connect(self.visualizer.clearPlot)
        self.buttonRowLayout.addWidget(self.bt_clearPlot)

        self.selfLayout.addLayout(self.buttonRowLayout)

    def handlePoint(self, point) -> None:
        pass

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event QCloseEvent): The QCloseEvent.
        """
        logger.debug(f"closeEvent in {__class__.__name__}")


class Visualizer(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements."""

        self.plot = Q3DScatter()
        self.plot.setAspectRatio(1.0)
        self.plot.setShadowQuality(Q3DScatter.ShadowQuality.ShadowQualityNone)

        self.selfLayout = QVBoxLayout(self)
        self.selfLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.selfLayout.setContentsMargins(10, 10, 10, 10)

        winCont = QWidget.createWindowContainer(self.plot)
        # TODO: There needs to be a better way for scaling this
        winCont.setFixedHeight(500)
        self.selfLayout.addWidget(winCont)

    def clearPlot(self) -> None:
        seriesList = self.plot.seriesList()
        if len(seriesList) == 2:
            dataProxy = seriesList[1].dataProxy()
            if dataProxy:
                dataProxy.resetArray([])

    # TODO: More here like adding data and stuff
