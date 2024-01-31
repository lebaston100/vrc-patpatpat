from typing import TYPE_CHECKING, Type, TypeVar

from PyQt6.QtCore import QObject

from utils import LoggerClass

if TYPE_CHECKING:
    from modules.GlobalConfig import GlobalConfigSingleton

logger = LoggerClass.getSubLogger(__name__)

"""
Using the factory pattern without ABC because it's
a mess when combining with QObject
"""

T = TypeVar('T', bound='GlobalConfigSingleton')


class ISolver():
    """ The interface """

    def solve(self):
        """ A generic solve method to be reimplemented"""
        raise NotImplementedError


class LinearSolver(ISolver, QObject):
    def __init__(self, config) -> None:
        logger.debug(config)
        super().__init__()

    def solve(self):
        logger.debug(f"Hello from solve() in {self.__class__.__name__}")


class MlatSolver(ISolver, QObject):
    def __init__(self, config) -> None:
        logger.debug(config)
        super().__init__()


class SolverFactory:
    @staticmethod
    def build_solver(solverType) -> \
            Type[LinearSolver] | Type[MlatSolver] | None:
        match solverType:
            case "Linear":
                return LinearSolver
            case "Mlat":
                return MlatSolver


class SolverRunner(QObject):
    def __init__(self, config) -> None:
        """This object is running inside the thread and manages
        all the solvers
        """
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__()
        # logger.debug(config)

        self._solvers: list[Type[LinearSolver] | Type[MlatSolver]] = []


if __name__ == "__main__":
    from GlobalConfig import config
    solverClass = SolverFactory.build_solver("mlat")
    if solverClass is not None:
        solver = solverClass(config)
        solver.solve()
