"""This module handles everything related to running solvers"""

import time

from PyQt6.QtCore import QObject, Qt, QThread, QTimer
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtCore import pyqtSlot as QSlot
from PyQt6.QtGui import QVector3D

from modules import config
from modules.AvatarPoint import AvatarPointSphere
from modules.Motor import Motor
from modules.Solver import SolverFactory
from utils import ConfigTemplate, LoggerClass, threadAsStr

logger = LoggerClass.getSubLogger(__name__)


class ContactGroup(QObject):
    dataRxStateChanged = QSignal(bool)
    avatarPointAdded = QSignal(object)
    avatarPointRemoved = QSignal(object)
    motorPwmChanged = QSignal(int, int, int)
    strengthSliderValueChanged = QSignal(int)
    newPointSolved = QSignal(QVector3D, int)
    openSettings = QSignal()

    def __init__(self, configKey) -> None:
        logger.debug(f"Creating {__class__.__name__}({configKey})")
        super().__init__()
        self._configKey = configKey

        self.motors: list[Motor] = []
        self.avatarPoints: list[AvatarPointSphere] = []

        self._currentDataState = False
        self._dataTimer = QTimer()
        self._dataTimer.timeout.connect(self._checkDataTimeout)
        self._dataTimer.start(200)

    def setup(self) -> None:
        try:
            self._config = config.get(self._configKey)
            self._id = self._config["id"]
            self._name = self._config["name"]

            for motor in self._config["motors"]:
                newMotor = Motor(motor)
                newMotor.motorPwmChanged.connect(self.motorPwmChanged)
                self.motors.append(newMotor)

            for avatarPoint in self._config["avatarPoints"]:
                newAvatarPoint = AvatarPointSphere(avatarPoint)
                self.avatarPoints.append(newAvatarPoint)
                self.avatarPointAdded.emit(newAvatarPoint)

            solverType = self._config["solver"]["solverType"]
            solverClass = SolverFactory.fromType(solverType)
            if solverClass:
                self.solver = solverClass(
                    self.motors, self.avatarPoints, self._configKey)
                self.strengthSliderValueChanged.connect(
                    self.solver.setStrength)
                self.solver.newPointSolved.connect(self.newPointSolved)
                self.solver.setup()
            else:
                logger.error("Unknown solver type specified")
        except Exception as E:
            logger.exception(E)

    def _checkDataTimeout(self) -> None:
        """Calculate if data for this group has recently come in.
        """
        # TODO: This also needs some rework as all other timeout checkers
        now = time.time()
        currentState = any(now - obj.lastValueTs <=
                           0.5 for obj in self.avatarPoints)
        if self._currentDataState != currentState:
            self._currentDataState = currentState
            self.dataRxStateChanged.emit(self._currentDataState)

    def close(self) -> None:
        """Closes everything we own and care for."""
        logger.debug(f"Stopping {__class__.__name__}({self._configKey})")
        for avatarPoint in self.avatarPoints:
            self.avatarPointRemoved.emit(avatarPoint)
        self.avatarPoints = []

    def __repr__(self) -> str:
        return self.__class__.__name__ + ":" + ";"\
            .join([f"{key}={str(val)}" for key, val in self.__dict__.items()])


class ContactGroupManager(QObject):
    registerAvatarPoint = QSignal(str)
    unregisterAvatarPoint = QSignal(str)
    tickSkipped = QSignal()  # ??
    motorPwmChanged = QSignal(int, int, int)
    solverDone = QSignal()
    contactGroupListChanged = QSignal(dict)
    currentTpsChanged = QSignal(int)
    _tpsSettingChanged = QSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        logger.debug(f"Creating {__class__.__name__}")
        super().__init__(parent)
        self._configKey = "groups"
        self.contactGroups: dict[int, ContactGroup] = {}
        self._avatarPoints: dict[str, list[AvatarPointSphere]] = {}

        self.workerThread = QThread()
        self.worker = ContactGroupSolverWorker(self)

        self.workerThread.started.connect(self.worker.startTimer)
        self.workerThread.finished.connect(self.worker.stopTimer)
        self.worker.moveToThread(self.workerThread)

        self.workerThread.start()

        config.configPathHasChanged.connect(self._handleConfigPathChange)
        config.configRootUpdateDone.connect(self._handleConfigRootChange)
        config.configPathWasDeleted.connect(self._handleConfigPathDeleted)

    def createAllContactGroupsFromConfig(self) -> None:
        """Create all ContactGroup objects from config file"""
        groups = config.get(self._configKey)
        for key, group in groups.items():
            newGroup = self._contactGroupFactory(f"{self._configKey}.{key}")
            self.contactGroups[group["id"]] = newGroup
        self.contactGroupListChanged.emit(self.contactGroups)

    def _contactGroupFactory(self, key: str) -> ContactGroup:
        group = ContactGroup(key)
        group.motorPwmChanged.connect(self.motorPwmChanged)
        group.avatarPointAdded.connect(self.avatarPointAdded)
        group.avatarPointRemoved.connect(self.avatarPointRemoved)
        group.setup()
        return group

    def avatarPointAdded(self, avatarPoint: AvatarPointSphere) -> None:
        """Adds a receiver id to the LUT and adds it to the VRC filter.

        Args:
            avatarPoint (AvatarPointSphere): The new AvatarPointSphere
        """
        if not avatarPoint.receiverId in self._avatarPoints:
            self.registerAvatarPoint.emit(avatarPoint.receiverId)
            self._avatarPoints[avatarPoint.receiverId] = []
        self._avatarPoints[avatarPoint.receiverId].append(avatarPoint)
        # logger.debug(self._avatarPoints)

    def avatarPointRemoved(self, avatarPoint: AvatarPointSphere) -> None:
        """Removes a receiver id from the LUT and unregisters it from
        the VRC filter.

        Args:
            avatarPoint (AvatarPointSphere): The AvatarPointSphere
                beeing deleted. 
        """
        if avatarPoint.receiverId in self._avatarPoints and \
                avatarPoint in self._avatarPoints[avatarPoint.receiverId]:
            self._avatarPoints[avatarPoint.receiverId].remove(avatarPoint)
            if not len(self._avatarPoints[avatarPoint.receiverId]):
                self.unregisterAvatarPoint.emit(avatarPoint.receiverId)
                self._avatarPoints.pop(avatarPoint.receiverId)
        # logger.debug(self._avatarPoints)

    @QSlot(float, str, list)
    def onVrcContact(self, ts: float, addr: str, params: list) -> None:
        """Distibute data coming from vrc to the ContactPoints.

        Args:
            ts (float): The osc message creation time
            addr (str): The full osc path
            params (list): The osc message parameter list
        """
        contactName = addr[19:]
        # logger.debug(
        # f"osc @ {ts}: addr={addr} msg={str(params)} "
        # f"contactName = {contactName}")
        if contactName in self._avatarPoints:
            for point in self._avatarPoints[contactName]:
                point.vrcContact(ts, params)

    @QSlot(str)
    def _handleConfigPathChange(self, path: str) -> None:
        if path == "program.mainTps":
            if self.workerThread:
                self.workerThread.quit()
                self.workerThread.wait()
            self.workerThread.start()

    @QSlot(str)
    def _handleConfigRootChange(self, path: str) -> None:
        """Handles changes to the config related to ContactGroups.

        Args:
            path (str): The config key of the group that has been edited.
        """
        if path.startswith("groups.group"):
            group = config.get(path)
            if not group:
                return

            fireSettings = False
            groupId = group["id"]
            if groupId in self.contactGroups:
                # Existing group, close
                self.contactGroups[groupId].close()
            else:
                fireSettings = True

            newGroup = self._contactGroupFactory(path)
            self.contactGroups[group["id"]] = newGroup
            self.contactGroupListChanged.emit(self.contactGroups)
            if fireSettings:
                newGroup.openSettings.emit()

    @QSlot(str)
    def _handleConfigPathDeleted(self, path: str) -> None:
        if path.startswith("groups.group"):
            groupId = int(path.removeprefix("groups.group"))
            self.contactGroups[groupId].close()
            del self.contactGroups[groupId]
            self.contactGroupListChanged.emit(self.contactGroups)

    @QSlot()
    def createEmptyGroup(self) -> None:
        newContactGroupId = self._getNewContactGroupId()
        newContactGroupKey = f"group{newContactGroupId}"
        newContactFullGroupKey = f"groups.{newContactGroupKey}"
        newContactGroupData = ConfigTemplate.TEMPLATE["groups"]["group0"]
        newContactGroupData["id"] = newContactGroupId
        newContactGroupData["name"] = f"New Group {newContactGroupId}"
        config.set(newContactFullGroupKey, newContactGroupData)
        self._handleConfigRootChange(newContactFullGroupKey)

    def _getNewContactGroupId(self) -> int:
        """Calculates an available index for a new device

        Returns:
            int: The new device index
        """
        if contactGroups := config.get("groups"):
            return max([d["id"] for d in contactGroups.values()]) + 1
        return 0

    def close(self) -> None:
        """Closes everything we own and care for."""
        logger.debug(f"Stopping {__class__.__name__}")
        if self.workerThread:
            self.workerThread.quit()
            self.workerThread.wait()
        for contactGroup in self.contactGroups.values():
            contactGroup.close()

    def __repr__(self) -> str:
        return self.__class__.__name__ + ":" + ";"\
            .join([f"{key}={str(val)}" for key, val in self.__dict__.items()])


class ContactGroupSolverWorker(QObject):
    def __init__(self, manager: ContactGroupManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._skipflag = False
        self._tpsCounter = 1000

    @QSlot()
    def startTimer(self):
        logger.debug(f"startTimer in {__class__.__name__} with "
                     f"pid={threadAsStr(self.thread())}")

        # Setup solver runner timer
        if not hasattr(self, "_timer"):
            self._timer = QTimer(self)
            self._timer.setTimerType(Qt.TimerType.PreciseTimer)
            self._timer.timeout.connect(self.tick)
        else:
            self._timer.stop()

        # Setup tps watcher timer
        if not hasattr(self, "_tpsStatTimer"):
            self._tpsStatTimer = QTimer(self)
            self._tpsStatTimer.timeout.connect(self._calcTps)
            self._tpsStatTimer.start(1000)

        # Calculate timer time from TPS and start timer
        self.tps = config.get("program.mainTps", 30)
        loopTimeMs: float = 1000/self.tps
        self.tickTimeNs = 1e9/self.tps
        logger.debug(f"Calculated tick time: "
                     f"{round(loopTimeMs)}ms / {self.tickTimeNs}ns")
        self._timer.start(round(loopTimeMs))

    @QSlot()
    def _calcTps(self):
        """Calculate and show the number of ticks in the last 1 seconds.
        """
        # logger.debug(f"ticks in the last 1000ms: {self._tpsCounter}")
        if self._tpsCounter < self.tps-1:
            logger.debug(f"TPS below setpoint! {self._tpsCounter} tps")
        self._manager.currentTpsChanged.emit(self._tpsCounter)
        self._tpsCounter = 0

    @QSlot()
    def stopTimer(self):
        logger.debug(f"stopTimer in {__class__.__name__}")
        if hasattr(self, "_timer"):
            self._timer.stop()
        if hasattr(self, "_tpsStatTimer"):
            self._tpsStatTimer.stop()
            del self._tpsStatTimer

    @QSlot()
    def tick(self):
        startTime = time.perf_counter_ns()
        if self._skipflag:
            self._skipflag = False
            return

        # Run solver
        try:
            for group in self._manager.contactGroups.values():
                group.solver.solve()
        except Exception as E:
            logger.exception(E)

        self._manager.solverDone.emit()
        self._tpsCounter += 1
        stopTime = time.perf_counter_ns()
        tickTime = stopTime - startTime
        if tickTime >= self.tickTimeNs:
            logger.warn("Skipping next tick!")
            self._skipflag = True
            self._manager.tickSkipped.emit()
        # logger.debug(f"Tick time: {tickTime/1e6} ms")


if __name__ == "__main__":
    print("There is no point running this file directly")
