from typing import Type

from PyQt6.QtCore import QObject

from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)

"""
Using the factory pattern without ABC because it's
a mess when combining with QObject
"""


class ISolver():
    """ The interface """

    def solve(self):
        """ A generic solve method to be reimplemented"""
        raise NotImplementedError


class LinearSolver(ISolver, QObject):
    def __init__(self, config) -> None:
        print(config)
        super().__init__()

    def solve(self):
        print(f"Hello from solve() in {self.__class__.__name__}")


class MlatSolver(ISolver, QObject):
    def __init__(self, config) -> None:
        print(config)
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


if __name__ == "__main__":
    solverClass = SolverFactory.build_solver("mlat")
    if solverClass is not None:
        solver = solverClass({"test": "val"})
        solver.solve()
