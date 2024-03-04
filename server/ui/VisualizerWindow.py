from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSlot as QSlot
from PyQt6.QtDataVisualization import (Q3DScatter, QScatter3DSeries,
                                       QScatterDataItem, QScatterDataProxy)
from PyQt6.QtGui import QCloseEvent, QColor, QColorConstants, QVector3D
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                             QWidget)

from modules.ContactGroup import ContactGroup
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class VisualizerWindow(QWidget):
    def __init__(self, groupRef: ContactGroup, *args, **kwargs) -> None:
        """Initialize the 3d visualizer window"""
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args, **kwargs)
        self._contactGroupRef = groupRef

        self.buildUi()

    def buildUi(self) -> None:
        """Initialize UI elements."""
        self.setWindowTitle(f"{self._contactGroupRef._name} - 3D Visualizer")
        self.setObjectName(__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(500, 500)

        self.selfLayout = QVBoxLayout(self)
        self.buttonRowLayout = QHBoxLayout()

        self.visualizer = Visualizer(self._contactGroupRef)
        self.selfLayout.addWidget(self.visualizer)

        self.bt_clearPlot = QPushButton("Clear Plot")
        self.bt_clearPlot.clicked.connect(self.visualizer.clearPlot)
        self.buttonRowLayout.addWidget(self.bt_clearPlot)

        self.selfLayout.addLayout(self.buttonRowLayout)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event cleanly.

        Args:
            event QCloseEvent): The QCloseEvent.
        """
        logger.debug(f"closeEvent in {__class__.__name__}")


class Visualizer(QWidget):
    def __init__(self, groupRef: ContactGroup) -> None:
        super().__init__()

        self._series: list[tuple[QScatter3DSeries, bool]] = []
        self._trailLength = 150
        self._contactGroupRef = groupRef

        self.buildUi()
        self._drawScalingPoints()
        # TODO: The solver should not have to care about the index
        self._createSeries(
            [motor.point for motor in self._contactGroupRef.motors],
            False, QColorConstants.Green, 0.05)
        self._createSeries(
            [point for point in self._contactGroupRef.avatarPoints],
            False, QColorConstants.Blue, 0.05)

    def buildUi(self) -> None:
        """Initialize UI elements."""

        self.plot = Q3DScatter()
        self.plot.setAspectRatio(1.0)
        self.plot.setShadowQuality(Q3DScatter.ShadowQuality.ShadowQualityNone)

        self.selfLayout = QVBoxLayout(self)
        self.selfLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.selfLayout.setContentsMargins(0, 0, 0, 0)

        winCont = QWidget.createWindowContainer(self.plot)
        # TODO: There needs to be a better way for scaling this
        winCont.setFixedHeight(500)
        self.selfLayout.addWidget(winCont)

    def clearPlot(self) -> None:
        """Clears all QScatter3DSeries data where dynamic flag is set"""
        for series, isDynamic in self._series:
            if isDynamic:
                if dataProxy := series.dataProxy():
                    dataProxy.resetArray([])

    def _drawScalingPoints(self) -> None:
        """Draws some initial points to have a static reference.
        This is basically a 3d bounding box."""
        avatarPoints = self._contactGroupRef.avatarPoints
        minPoint = QVector3D()
        maxPoint = QVector3D()

        for point in avatarPoints:
            minPoint.setX(min(minPoint.x(), point.x()))
            minPoint.setY(min(minPoint.y(), point.y()))
            minPoint.setZ(min(minPoint.z(), point.z()))
            maxPoint.setX(max(maxPoint.x(), point.x()))
            maxPoint.setY(max(maxPoint.y(), point.y()))
            maxPoint.setZ(max(maxPoint.z(), point.z()))

        newId = self._createSeries(
            [minPoint, maxPoint], False, QColorConstants.White, 0.01)
        logger.debug(f"Created scaling series with index {newId}")

    @QSlot(QVector3D, int)
    def handleDataPoint(self, point: QVector3D, id: int = 0) -> None:
        """Adds a single point to the plot.

        Args:
            point (QVector3D): The point to add.
        """
        # check if id is a valid series
        if 0 <= id >= len(self._series):
            newId = self._createSeries([], True)
            logger.debug(f"Created new dynamic series with index {newId}")

        # check trail
        dataProxy = self._series[id][0].dataProxy()
        if not dataProxy:
            return
        if dataProxy.itemCount() > self._trailLength:
            dataProxy.removeItems(0, 1)

        # add point to dataProxy of QScatter3DSeries
        dataProxy.addItem(QScatterDataItem(point))

    def _createSeries(self, points: list[QVector3D],
                      isDynamic: bool = False,
                      pointColor: QColor | Qt.GlobalColor
                      | int = QColorConstants.Red,
                      pointSize: float = 0.05) -> int:
        """Creates a new series and adds it to the plot.

        Args:
            points (list[QVector3D]): The points to add to the new series.
                Pass [] if only an empty series should be created.
            isDynamic (bool, optional): Flag if the new series will be
                modified at runtime. Defaults to False.
            pointColor (QColor | Qt.GlobalColor | int, optional): The
                point colors. Defaults to QColorConstants.Red.
            pointSize (float, optional): The size of the points.
                Defaults to 0.05.

        Returns:
            int: The index of the newly created scatter series.
        """
        series = self._scatterSeriesFactory()
        series.setBaseColor(pointColor)
        series.setItemSize(pointSize)
        if points and (dataProxy := series.dataProxy()):
            dataProxy.addItems([QScatterDataItem(p) for p in points])
        self._series.append((series, isDynamic))
        self.plot.addSeries(series)
        return len(self._series)-1

    def _scatterSeriesFactory(self) -> QScatter3DSeries:
        proxy = QScatterDataProxy()
        series = QScatter3DSeries()
        series.setItemSize(0.05)
        series.setBaseColor(QColorConstants.Red)
        series.setDataProxy(proxy)
        return series