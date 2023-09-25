from patpatpat import getSubLogger

logger = getSubLogger(__name__)


class LoggerTestClass():
    def __init__(self) -> None:
        """Will generate a few logging messages for testing"""
        logger.debug("debug from submodule")
        logger.info("info from submodule")
        logger.error("error from submodule")
