"""
This module provides functionality to read the OSC parameters of all
available VRC avatars from the local installation.
"""

import json
import os
import pathlib
from dataclasses import dataclass, field
from typing import Self

vrcInternals = ["VRCEmote", "InStation", "Seated", "GestureRightWeight", "GestureLeftWeight", "GestureRight", "GestureLeft", "Viseme", "IsOnFriendsList", "EyeHeightAsMeters", "EyeHeightAsPercent",
                "ScaleModified", "ScaleFactorInverse", "ScaleFactor", "VelocityMagnitude", "Earmuffs", "Voice", "MuteSelf", "VRMode", "TrackingType", "Upright", "AFK", "Grounded", "AngularY", "VelocityZ", "VelocityY", "VelocityX"]


@dataclass
class VrcAvatar:
    """
    A class to represent a VRC Avatar.

    Attributes:
        id (str): The id of the avatar.
        name (str): The name of the avatar.
        parameters (list): The parameters of the avatar.
    """

    aid: str = ""
    name: str = ""
    inputParameters: list = field(default_factory=list)
    outputParameters: list = field(default_factory=list)

    @classmethod
    def fromFile(cls, filePath: pathlib.Path) -> Self:
        """Load avatar data from a JSON file.

        Args:
            filePath (Path): The path of the JSON file.

        Returns:
            VrcAvatar: The avatar object with loaded data.
        """
        data = cls._loadJson(filePath)
        aid = data.get("id", "")
        name = data.get("name", "")
        inputParameters = []
        outputParameters = []

        parameters = data.get("parameters", [])
        if parameters:
            inputParameters = list(
                map(
                    lambda x: {"name": x["name"], **x["input"]},
                    filter(lambda x: "input" in x, parameters),
                )
            )
            outputParameters = list(
                map(
                    lambda x: {"name": x["name"], **x["output"]},
                    filter(lambda x: "output" in x, parameters),
                )
            )

        return cls(aid, name, inputParameters, outputParameters)

    @staticmethod
    def _loadJson(filePath: pathlib.Path) -> dict:
        """Load data from a JSON file.

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
    """Get all available VRC avatars from the local installation.

    Returns:
        list[VrcAvatar] | list: A list of VRC avatars if available, else
        an empty list.
    """
    appdata = os.getenv("APPDATA")
    if appdata:
        vrcfolder = pathlib.Path(
            appdata
        ).joinpath("..", "LocalLow", "VRChat", "VRChat", "OSC")
        return [VrcAvatar.fromFile(f) for f in vrcfolder.rglob("avtr_*.json")]
    return []


if __name__ == "__main__":
    avatars = getVrcAvatars()
    for avatar in avatars:
        print(json.dumps(avatar.__dict__, indent=4))
