from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt
from PyQt6.QtDataVisualization import Q3DScatter, QScatter3DSeries, QScatterDataProxy, QScatterDataItem
from PyQt6.QtGui import QColorConstants
from server import Server
from guiClasses import CGui2Row
from config import Config
import time
import sys
import logging
import pathlib

logging.basicConfig(level=logging.DEBUG)

# get local directory as path object
LOCALDIR = pathlib.Path(__file__).parent.resolve()

class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.slider_strength = None
        self.prev_patpatpat_status = False
        self.prev_vrchat_status = False

        self.setWindowTitle("vrc-patpatpat 0.2")
        with open("global.css","r") as file:
            self.setStyleSheet(file.read())

        layoutMain = QVBoxLayout()
        layoutMain.setContentsMargins(0, 0, 0, 0)

        box = QWidget()
        box.setObjectName("mainbackground")

        # create all the gui rows
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.createGuiHardwareStatus())
        layout.addWidget(self.createGuiBattery())
        layout.addWidget(self.createGuiVrcRecvStatus())
        layout.addWidget(self.createGuiSettingsSlider())
        layout.addWidget(self.createGuiButtonRow1())
        layout.addWidget(self.createGuiVisualizer())

        # create config handler
        self.config = Config(file=LOCALDIR / "patpatpat.cfg")
        # create server part
        self.server = Server(self)

        box.setLayout(layout)
        layoutMain.addWidget(box)
        self.setLayout(layoutMain)

# Row 1: Hardware connection status "led"
    def createGuiHardwareStatus(self) -> CGui2Row:
        self.status_hardware_connection = QLabel(" ⬤")

        row = CGui2Row(title="patpatpat connection", content=self.status_hardware_connection)
        return row

    def setGuiHardwareConnectionStatus(self, status: bool) -> None:
        if self.prev_patpatpat_status != status:
            self.prev_patpatpat_status = status
            self.status_hardware_connection.setStyleSheet("color: #29b980; font-size: 30px;" if status else "color: #b94029; font-size: 30px;")

            self.test_right_button.setDisabled(not status)
            self.test_left_button.setDisabled(not status)

# Row 2: Hardware battery voltage
    def createGuiBattery(self) -> CGui2Row:
        self.battery_text = QLabel("-")

        row = CGui2Row(title="patpatpat battery", content=self.battery_text)
        return row

    def setGuiBattery(self, val):
        self.battery_text.setText(str(val))

# Row 3: VRC data receive status
    def createGuiVrcRecvStatus(self) -> CGui2Row:
        self.status_vrchat_connection = QLabel("  ⬤")

        row = CGui2Row(title="VRChat data", content=self.status_vrchat_connection)
        return row

    def setGuiVrcRecvStatus(self, status: bool) -> None:
        if self.prev_vrchat_status != status:
            self.prev_vrchat_status = status
            self.status_vrchat_connection.setStyleSheet("color: #29b980; font-size: 30px;" if status else "color: #b94029; font-size: 30px;")

# Row 4: A slider that currently does nothing
    def createGuiSettingsSlider(self) -> CGui2Row:
        self.slider_strength = QSlider(Qt.Orientation.Horizontal)
        self.slider_strength.setMaximumWidth(200)
        self.slider_strength.setMinimum(0)
        self.slider_strength.setMaximum(100)
        self.slider_strength.setValue(50)

        row = CGui2Row(title="Intensity", content=self.slider_strength, AlignRight=False, DefaultColor=False)
        return row

    def getGuiSettingsSlider(self) -> float:
        if self.slider_strength is None:
            return 0
        return self.slider_strength.value() / 100.0

# Row 5: 2 test buttons and one button to clear the plot
    def createGuiButtonRow1(self) -> QWidget:
        box = QWidget()
        box.setObjectName("section")
        box.setFixedHeight(140)

        layoutH = QHBoxLayout()
        layoutV = QVBoxLayout()
        layoutV.setContentsMargins(20, 20, 20, 20)

        self.test_left_button = QPushButton("Pat left")
        self.test_left_button.clicked.connect(self.signalGuiButtonPatLeft)
        self.test_left_button.setDisabled(True)
        layoutH.addWidget(self.test_left_button)

        self.test_right_button = QPushButton("Pat right")
        self.test_right_button.clicked.connect(self.signalGuiButtonPatRight)
        self.test_right_button.setDisabled(True)
        layoutH.addWidget(self.test_right_button)

        self.clear_plot_button = QPushButton("Clear Plot")
        self.clear_plot_button.clicked.connect(self.signalGuiClearVisualizerPlot)
        layoutH.addWidget(self.clear_plot_button)

        info_label = QLabel("Test hardware")
        info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_label.setFixedHeight(40)
        layoutV.addWidget(info_label)
        layoutV.addItem(layoutH)

        box.setLayout(layoutV)
        return box

    def signalGuiButtonPatLeft(self) -> None:
        logging.debug("Pat left")
        self.server.oscMotorTxData[0] = 0
        time.sleep(1)
        self.server.oscMotorTxData[0] = 255

    def signalGuiButtonPatRight(self) -> None:
        logging.debug("Pat right")
        self.server.oscMotorTxData[1] = 0
        time.sleep(1)
        self.server.oscMotorTxData[1] = 255

    def signalGuiClearVisualizerPlot(self) -> None:
        self.visualizerPlot.seriesList()[1].dataProxy().resetArray([])

# Row 6: The 3D visualizer
    def createGuiVisualizer(self) -> QWidget:
        self.visualizerPlot = Q3DScatter()
        self.visualizerPlot.setAspectRatio(1.0)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)

        info_label = QLabel("3D View")
        info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_label.setFixedHeight(40)
        layout.addWidget(info_label)

        t = QWidget.createWindowContainer(self.visualizerPlot)
        t.setObjectName("section")
        t.setFixedHeight(700)
        layout.addWidget(t)

        box = QWidget()
        box.setObjectName("section")
        box.setLayout(layout)
        return box

    def closeEvent(self, _) -> None:
        self.server.shutdown()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.setFixedSize(1200, 1200)
    window.show()
    sys.exit(app.exec())