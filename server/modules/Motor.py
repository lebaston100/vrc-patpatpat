from math import ceil

from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSignal as QSignal

from modules.Points import Sphere3D
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class Motor(QObject):
    """Represents a motor attached to an ESP Pin (Channel)"""
    speedChanged = QSignal(int, int, float)
    motorPwmChanged = QSignal(int, int, int)

    def __init__(self, settings: dict, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._name: str = settings["name"]
        self._espAddr: list[int] = settings["espAddr"]
        self._minPwm: int = settings["minPwm"]
        self._maxPwm: int = settings["maxPwm"]
        self.point = Sphere3D(self._name)
        self.point.radius = settings["r"]
        self.point.xyz = settings["xyz"]
        self.currentSpeed: float = 0.0
        self.currentPWM: int = 0

    def setSpeed(self, newSpeed: float) -> None:
        """Takes a normalized speed from 0.0-1.0 and converts it to the
        required pwm value.

        It handles the dead-band between 0 and self._minPwm and
        also scales the value to the required max pwm.
        That way we can have one Motor on a 8 bit channel while
        another on a 10 bit one.

        Args:
            newSpeed (float): The speed to set
        """
        motorPwm = min(ceil(self._maxPwm * newSpeed), self._maxPwm)
        pwm = self._minPwm if (motorPwm < self._minPwm
                               and motorPwm > 0) else motorPwm
        self.setPwm(pwm)
        self.speedChanged.emit(*self._espAddr, newSpeed)

    def fadeOut(self):
        if self.currentPWM:
            self.setPwm(max(self.currentPWM-6, 0))

    def setPwm(self, pwm: int) -> None:
        self.currentPWM = pwm
        self.motorPwmChanged.emit(*self._espAddr, pwm)

    def __repr__(self) -> str:
        return self.__class__.__name__ + ":" + ";"\
            .join([f"{key}={str(val)}" for key, val in self.__dict__.items()])
