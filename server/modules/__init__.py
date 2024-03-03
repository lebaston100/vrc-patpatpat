"""Exposes a global config class instance that can be used anywhere
where access to it is needed.

Exposes:
    config
    OptionAdapter
"""
from .GlobalConfig import config

from .AvatarPoint import AvatarPointSphere
from .ContactGroup import ContactGroup, ContactGroupManager
from .HardwareDevice import HardwareDevice
from .HwManager import HwManager
from .Motor import Motor
from .OptionAdapter import OptionAdapter
from .OscMessageTypes import *
from .Points import Sphere3D
from .Server import ServerSingleton
from .Solver import SolverFactory
from .VrcConnector import VrcConnectorImpl
