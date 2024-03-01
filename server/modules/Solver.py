import time

from multilateration import Engine
from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSlot as QSlot

from modules import config
from modules.AvatarPoint import AvatarPointSphere
from modules.Motor import Motor
from utils import LoggerClass, SolverType

logger = LoggerClass.getSubLogger(__name__)


class ISolver(QObject):
    """The interface/base class."""

    def __init__(self, avatarPoints: AvatarPointSphere,
                 motors: Motor,
                 configKey: str) -> None:
        super().__init__()
        self._avatarPoints = avatarPoints
        self._motors = motors
        self._configKey = configKey
        self._loadConfig()
        # logger.debug(self)

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
        return __class__.__name__ + ":" + ";"\
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

    @QSlot(int)
    def setStrength(self, strength: int) -> None:
        logger.debug(f"strength was changed to {strength}")
        config.set(f"{self._configKey}.solver.strength", strength)
        self._loadConfig()

    def solve(self) -> None:
        # logger.debug(f"Hello from solve() in {self.__class__.__name__}")
        # time.sleep(0.05)  # simulate very heavy calculation
        # TODO: MLAT implementation
        pass


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
