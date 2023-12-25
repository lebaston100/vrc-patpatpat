from PyQt6.QtGui import QVector3D


class Point3D(QVector3D):
    """A 3D Point with a name and radius."""

    def __init__(self, name: str = "", radius: float = 0,
                 x: float = 0, y: float = 0, z: float = 0, *args, **kwargs):
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

    def setXYZ(self, xyz: list):
        self.setX(xyz[0])
        self.setY(xyz[1])
        self.setZ(xyz[2])

    def setRadius(self, radius: float = 0.0):
        self._radius = radius
