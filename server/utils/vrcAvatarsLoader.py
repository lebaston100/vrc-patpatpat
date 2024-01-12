"""
This module provides functionality to read the OSC parameters of all available
VRC avatars from the local installation.
"""

import json
import os
import pathlib
from dataclasses import dataclass, field


@dataclass
class VrcAvatar:
    """
    A class to represent a VRC Avatar.

    Attributes:
        id (str): The id of the avatar.
        name (str): The name of the avatar.
        parameters (list): The parameters of the avatar.
    """

    id: str = ""
    name: str = ""
    parameters: list = field(default_factory=list)

    def load(self, filePath):
        """
        Load avatar data from a JSON file.

        Args:
            filePath (Path): The path of the JSON file.

        Returns:
            VrcAvatar: The avatar object with loaded data.
        """

        data = self._loadJson(filePath)
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.parameters = data.get("parameters", [])
        return self

    def _loadJson(self, filePath) -> dict:
        """
        Load data from a JSON file.

        Args:
            filePath (Path): The path of the JSON file.

        Returns:
            dict: The data loaded from the JSON file.
        """

        try:
            with filePath.open(mode="r", encoding="utf-8-sig") as f:
                return json.load(f)
        except:
            return {}


def getVrcAvatars() -> list[VrcAvatar] | list:
    """
    Get all available VRC avatars from the local installation.

    Returns:
        list[VrcAvatar] | list: A list of VRC avatars if available, else
        an empty list.
    """

    appdata = os.getenv("APPDATA")
    if appdata:
        vrcfolder = pathlib.Path(
            appdata
        ).joinpath("..", "LocalLow", "VRChat", "VRChat", "OSC")
        return [VrcAvatar().load(f) for f in vrcfolder.rglob("avtr_*.json")]
    return []


if __name__ == "__main__":
    avatars = getVrcAvatars()
    for avatar in avatars:
        print(avatar.__dict__)
