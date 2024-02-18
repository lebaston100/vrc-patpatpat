import html
import logging
import logging.handlers
from collections.abc import Iterator
from logging import LogRecord, _levelToName, _nameToLevel

from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSignal as QSignal


class LoggerClass():
    __rootLogger = None

    @classmethod
    def getRootLogger(cls, filename: str = "customlog.log",
                      level=logging.DEBUG) -> logging.Logger:
        """Return the "root" logger.
        "root" because technically it is not the real root logger
        Returns the same logger if called repeatedly

        Args:
            level (logging.LEVEL, optional): The logging level.
                Defaults to logging.DEBUG.

        Returns:
            logging.Logger: The logging.Logger object.
        """
        # return existing logger if we ask for it, this is basically
        # a singleton now
        if cls.__rootLogger:
            return cls.__rootLogger

        # rotating log file handler
        fileLogHandler = logging.handlers.RotatingFileHandler(
            filename=filename,
            encoding="utf-8",
            maxBytes=16 * 1024 * 1024,  # 32 MiB
            backupCount=5,  # Rotate through 5 files
        )
        fileLogHandler.setLevel(level)
        fileLogHandler.setFormatter(logging.Formatter(
            "[{asctime}.{msecs:.0f}] [{levelname:<8}] {name}: {message}",
            datefmt="%Y-%m-%d %H:%M:%S", style="{"))

        # cmd output
        cmdLogHandler = logging.StreamHandler()
        cmdLogHandler.setLevel(level)
        cmdLogHandler.setFormatter(logging.Formatter(
            "[{relativeCreated:.3f}][{levelname:<5}][{name:<30}] {message}",
            style="{"))

        # setup main logger
        logger = logging.getLogger("ppp")
        logger.propagate = False
        logger.setLevel(level)
        logger.addHandler(fileLogHandler)
        logger.addHandler(cmdLogHandler)
        LoggerClass.attachLoggingLevels(logger)
        cls.__rootLogger = logger
        return logger

    @staticmethod
    def getSubLogger(name: str, level: str = "DEBUG") -> logging.Logger:
        """Return a usable logger for current submodule that is a child
        of our root logger "ppp".

        Args:
            name (str): Module name aka __name__
            level (str, optional): The log level to use for this logger.
                Defaults to "DEBUG".

        Returns:
            logging.Logger: A logging logger.
        """
        logger = logging.getLogger("ppp").getChild(name)
        logger.setLevel(logging.getLevelName(level))
        LoggerClass.attachLoggingLevels(logger)
        return logger

    @staticmethod
    def attachLoggingLevels(logger) -> None:
        for level in LoggerClass.getLoggingLevelStrings():
            setattr(logger, level, _nameToLevel[level])

    @staticmethod
    def getLoggingLevelStrings() -> Iterator[str]:
        """Return all available logging level as a generator.

        Yields:
            Iterator[str]: The log level string capitalized.
        """
        for level in _levelToName.values():
            if level == "NOTSET":
                continue
            yield level


class LogWindowSignaler(QObject):
    """Keeper of QSignals for the new-log-line Signal.
    Done because SingalLogHandler already inherits from logging.Handler
    and we need to subclass QObject for Signals to work
    Maybe we'll find a better way for this some day.
    For right now this works.

    Signals:
        newLogEntry(str): Emited when a new log entry was generated
    """
    newLogEntry = QSignal(str)

    def __init__(self) -> None:
        """Nothing to see here. super() boring.
        """

        super().__init__()


# a logging handler that emits the logged string to the QEvent
class SignalLogHandler(logging.Handler):
    """A custom logging Handler that emits the formated log lines from
    a QSignal.
    """

    def __init__(self, level=logging.DEBUG) -> None:
        """Initialize the log handler.

        Args:
            level (logging.LEVEL, optional): The log level to use
                for this logger. Defaults to logging.DEBUG.
        """
        super().__init__(level=level)
        self.signal = LogWindowSignaler()
        self.setFormatter(logging.Formatter(
            "[{asctime}.{msecs:.0f}] [{levelname:<8}] {name:<30}: {message}",
            datefmt="%Y-%m-%d %H:%M:%S", style="{"))

    def emit(self, record: LogRecord) -> None:
        """Generate signal when new LogRecord is created.

        Args:
            record (LogRecord): The LogRecord to emit
        """
        try:
            formatedText = html.escape(self.format(record))
            # text color red when WARN or above
            if record.levelno > 20:
                formatedText = f"<font color=\"Red\">{formatedText}</font>"
        except Exception:
            self.handleError(record)
        else:
            self.signal.newLogEntry.emit(formatedText)

    def changeLevel(self, level: str) -> None:
        """Change the level of logger.

        Args:
            level (str): The logging level to use
        """
        self.setLevel(logging.getLevelName(level))


if __name__ == "__main__":
    print("There is no point running this file directly")
