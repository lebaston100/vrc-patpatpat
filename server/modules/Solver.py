import time

from multilateration import Engine, Point
from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from PyQt6.QtGui import QVector3D

from modules import config
from modules.AvatarPoint import AvatarPointSphere
from modules.Motor import Motor
from utils import LoggerClass, SolverType

logger = LoggerClass.getSubLogger(__name__)


class ISolver(QObject):
    """The interface/base class."""
    newPointSolved = QSignal(object)

    def __init__(self, motors: list[Motor],
                 avatarPoints: list[AvatarPointSphere],
                 configKey: str) -> None:
        super().__init__()
        self._avatarPoints = avatarPoints
        self._motors = motors
        self._configKey = configKey
        self._loadConfig()
        logger.debug(self)

    def _loadConfig(self) -> None:
        self._config = config.get(f"{self._configKey}.solver")
        if not self._config:
            logger.error("Failed to load config for solver")

    def setup(self) -> None:
        """A generic setup method to be reimplemented."""
        raise NotImplementedError

    def setStrength(self, strength: int) -> None:
        """A generic setStrength method to be reimplemented."""
        raise NotImplementedError

    def solve(self) -> None:
        """A generic solve method to be reimplemented."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.__class__.__name__ + ":" + ";"\
            .join([f"{key}={str(val)}" for key, val in self.__dict__.items()])


class LinearSolver(ISolver):
    def __init__(self, *args) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args)

    def setup(self) -> None:
        pass

    @QSlot(int)
    def setStrength(self, strength: int) -> None:
        logger.debug(f"strength was changed to {strength}")
        config.set(f"{self._configKey}.solver.strength", strength)
        self._loadConfig()

    def solve(self) -> None:
        logger.debug(f"Hello from solve() in {self.__class__.__name__}")
        # TODO: Linear solver implementation


class MlatSolver(ISolver):
    def __init__(self, *args) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(*args)

    def setup(self) -> None:
        self.mlatEngine = Engine()

        # Create anchor points
        for avatarPoint in self._avatarPoints:
            self.mlatEngine.add_anchor(avatarPoint.receiverId, avatarPoint.xyz)

        # find center point for validation
        self._centerPoint = min(self._avatarPoints, key=lambda p: p.y())

    @QSlot(int)
    def setStrength(self, strength: int) -> None:
        """Update the strength value from the ui side

        Args:
            strength (int): The new strength percentage
        """
        logger.debug(f"strength was changed to {strength}%")
        config.set(f"{self._configKey}.solver.strength", strength)
        self._loadConfig()

    def solve(self) -> None:
        if not self._validatePointDataAge():
            return

        # Add point measures to solver
        for avatarPoint in self._avatarPoints:
            self.mlatEngine.add_measure_id(
                avatarPoint.receiverId, avatarPoint.lastValue)

        # Try to solve
        if not (solveResult := self.mlatEngine.solve()):
            logger.debug("Could not solve")
            return

        logger.debug(f"Sucessfully solved to {str(solveResult)}")

        solvedPoint = self._QVector3DfromMlatPoint(solveResult)

        self.newPointSolved.emit(solvedPoint)

        if not self._validateMlatPoint(solvedPoint):
            logger.debug(f"Validation failed for {solvedPoint}")
            return
        logger.debug(solvedPoint)

    def _validatePointDataAge(self) -> bool:
        """Check that all received points are fresh"""
        maxAge = time.time()-0.15
        return all(p.lastValueTs > maxAge for p in self._avatarPoints)

    def _QVector3DfromMlatPoint(self, point: Point):
        return QVector3D(point.x, point.y, point.z)

    def _validateMlatPoint(self, point: QVector3D) -> bool:
        """Validate that the calculcated point makes sense"""
        # distance from center point to calculcated point
        # <= center radius + some margin
        # and the point's y is not below half the radius of the center y
        center = self._centerPoint
        logger.debug(center.radius*1.2)
        logger.debug(center.distanceToPoint(point))
        logger.debug(point.y())
        logger.debug(center.y())
        logger.debug(center.radius*0.5)
        return center.distanceToPoint(point) <= center.radius*1.2 \
            and point.y() >= center.y()-center.radius*0.5


class SolverFactory:
    @staticmethod
    def fromType(solverType: SolverType) -> \
            type[LinearSolver] | type[MlatSolver] | None:
        match solverType:
            case SolverType.LINEAR:
                return LinearSolver
            case SolverType.MLAT:
                return MlatSolver


if __name__ == "__main__":
    print("There is no point running this file directly")
