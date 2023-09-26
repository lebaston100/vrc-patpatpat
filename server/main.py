import patpatpat
from patpatpat import ConfigHandler, LoggerTestClass

logger = patpatpat.getRootLogger()

logger.debug("debug from main")
logger.info("info from main")
logger.error("error from main")

LoggerTestClass()

config = ConfigHandler("test.config")
config.set("testkey", "testvalue")
