from math import ceil

from PyQt6.QtCore import QObject

from modules.Points import Sphere3D


class Motor(QObject):
    """Represents a motor attached to an ESP Pin (Channel)"""

    def __init__(self, settings: dict, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._name: str = settings["name"]
        self._espAddr: list[int] = settings["espAddr"]
        self._minPwm: int = settings["minPwm"]
        self._maxPwm: int = settings["maxPwm"]
        self._point = Sphere3D(self._name)
        self._point.setXYZ(settings["xyz"])

        self.currentPWM: int = 0

    def setSpeed(self, newSpeed: float) -> int:
        """Takes a normalized speed from 0-1 and converts it to the
            required pwm value.

            It handles the dead-band between 0 and self._minPwm and
            also scales the value to the required max pwm.
            That way we can have one Motor on a 8 bit channel while
            another on a 10 bit one.

        Args:
            newSpeed (float): The speed to set

        Return:
            int: The calculated PWM value
        """

        # little deadband in the middle, maybe not needed, not sure yet
        # distance = max(distance, 0.1)
        # this would invert the value, we should do this somewhere else!
        # motorPwm = self._maxPwm-min(ceil(self._maxPwm*newSpeed), self._maxPwm)
        motorPwm = min(ceil(self._maxPwm * newSpeed), self._maxPwm)
        self.currentPWM = self._minPwm if (motorPwm < self._minPwm
                                           and motorPwm > 0) else motorPwm
        return self.currentPWM
