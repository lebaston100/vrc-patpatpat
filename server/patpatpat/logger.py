import logging
import logging.handlers


def getRootLogger(level=logging.DEBUG) -> logging.Logger:
    """Return our main root logger

    Args:
        level (logging.LEVEL, optional): The logging level. Defaults to logging.DEBUG.

    Returns:
        logging.Logger: The logging.Logger object
    """
    # rotating log file handler
    fileLogHandler = logging.handlers.RotatingFileHandler(
        filename="vrc-patpatpat.log",
        encoding="utf-8",
        maxBytes=16 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    fileLogHandler.setLevel(level)
    fileLogHandler.setFormatter(logging.Formatter(
        "[{asctime}.{msecs:.0f}] [{levelname:<8}] {name}: {message}", datefmt="%Y-%m-%d %H:%M:%S", style="{"))

    # cmd output
    cmdLogHandler = logging.StreamHandler()
    cmdLogHandler.setLevel(level)
    cmdLogHandler.setFormatter(logging.Formatter(
        "[{relativeCreated:.3f}][{levelname:<5}][{name:<26}] {message}", style="{"))

    # setup main logger
    logger = logging.getLogger("patpatpat")
    logger.propagate = False
    logger.setLevel(level)
    logger.addHandler(fileLogHandler)
    logger.addHandler(cmdLogHandler)
    return logger


def getSubLogger(name: str, level: str = "DEBUG") -> logging.Logger:
    """Return a usable logger for current submodule that is a Child of
    our root logger "vrc-ppp"

    Args:
        name (str): Module name aka __name__
        level (str, optional): The log level to use for this logger. Defaults to "DEBUG".

    Returns:
        logging.Logger: A logging logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.getLevelName(level))
    return logger


if __name__ == "__main__":
    logging.error("There is no point running this file directly")
