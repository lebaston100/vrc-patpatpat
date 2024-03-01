from typing import Self, TypeVar

from multilateration import Point
from PyQt6.QtGui import QVector3D

T = TypeVar('T', bound='Sphere3D')


class Sphere3D(QVector3D):
    """A 3D Point with a name and radius."""

    def __init__(self, name: str = "", radius: float = 0,
                 x: float = 0, y: float = 0, z: float = 0,
                 *args, **kwargs) -> None:
        """Creates a new 3D Point.

        Args:
            name (str, optional): A name. Defaults to "".
            x (float, optional): X. Defaults to 0.
            y (float, optional): Y. Defaults to 0.
            z (float, optional): Z. Defaults to 0.
            radius (float, optional): Radius. Defaults to 0.
        """
        super().__init__(x, y, z)
        self._radius = radius
        self._name = name

    @property
    def point(self) -> Point:
        """Returns a multilateration-compatible point.
        Not sure if this of any use, but we can always remove it.

        Returns:
            Point: The multilateration.Point instance
        """
        return Point((self.x(), self.y(), self.z()))

    @property
    def xyz(self) -> tuple[float, ...]:
        return (self.x(), self.y(), self.z())

    @xyz.setter
    def xyz(self, xyz: list) -> Self:
        self.setX(xyz[0])
        self.setY(xyz[1])
        self.setZ(xyz[2])
        return self

    @property
    def radius(self):
        self._radius

    @radius.setter
    def radius(self, radius: float = 0.0) -> Self:
        self._radius = radius
        return self
