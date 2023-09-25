import patpatpat
from patpatpat import LoggerTestClass

logger = patpatpat.getRootLogger()

logger.debug("debug from main")
logger.info("info from main")
logger.error("error from main")

LoggerTestClass()
