from typing import Self, Type, TypeVar

from PyQt6.QtGui import QVector3D

T = TypeVar('T', bound='Sphere3D')


class Sphere3D(QVector3D):
    """A 3D Point with a name and radius."""

    @classmethod
    # TODO get data from config and pass to constructor
    def fromConfig(cls: Type[T], config, key: str) -> T:
        return cls()

    def __init__(self, name: str = "", radius: float = 0,
                 x: float = 0, y: float = 0, z: float = 0, *args, **kwargs) -> None:
        """Creates a new 3D Point.

        Args:
            name (str, optional): A name. Defaults to "".
            x (float, optional): X. Defaults to 0.
            y (float, optional): Y. Defaults to 0.
            z (float, optional): Z. Defaults to 0.
            radius (float, optional): Radius. Defaults to 0.
        """
        super().__init__(x, y, z, *args, **kwargs)
        self._radius = radius
        self._name = name

    def setXYZ(self, xyz: list) -> Self:
        self.setX(xyz[0])
        self.setY(xyz[1])
        self.setZ(xyz[2])
        return self

    def setRadius(self, radius: float = 0.0) -> Self:
        self._radius = radius
        return self
