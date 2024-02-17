from modules.Points import Sphere3D


class AvatarPoint(Sphere3D):
    def __init__(self, settings: dict, *args, **kwargs) -> None:
        self._name: str = settings["name"]
        self._receiverId: str = settings["receiverId"]
        self._xyz: list[int] = settings["xyz"]
        self._radius: float = settings["r"]
        super().__init__(self._name, self._radius, *args, **kwargs)
        self.setXYZ(self._xyz)
