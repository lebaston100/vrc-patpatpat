"""The main application window
"""

from ui import LogWindow, ToggleButton, StaticLabel
from PyQt6.QtWidgets import QMainWindow
from modules import config
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
