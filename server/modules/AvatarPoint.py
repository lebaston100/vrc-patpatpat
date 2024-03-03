from PyQt6.QtCore import QObject

from modules.Points import Sphere3D
from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class AvatarPointSphere(Sphere3D):
    def __init__(self, settings: dict, *args, **kwargs) -> None:
        self.name: str = settings["name"]
        self.radius: float = settings["r"]

        super().__init__(self.name, self.radius)

        self.xyz: tuple[float, ...] = settings["xyz"]
        self.receiverId: str = settings["receiverId"]
        self.lastValue = 0.0
        self.lastValueTs: float = 0.0

    def vrcContact(self, time: float, params: list):
        """The callback run by the ContactGroupManager when new data
        from VRC comes in for this contact receiver

        Args:
            time (float): The osc message creation time
            params (list): The osc parameters
        """
        try:
            self.lastValue = params[0]
            self.lastValueTs = time
        except Exception as E:
            logger.exception(E)

    def __repr__(self) -> str:
        return self.__class__.__name__ + ":" + ";"\
            .join([f"{key}={str(val)}" for key, val in self.__dict__.items()])
