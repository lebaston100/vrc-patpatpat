from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt
import time
import sys
import logging

class VisualizerWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()