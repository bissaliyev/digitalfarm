import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

fileHandler = logging.FileHandler("/home/pi/digitalfarm.log")
fileHandler.setFormatter(logFormatter)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)

logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

logger.info('Info Started Everyday script')
logger.debug('Debug Started Everyday script')
logger.error('Error Started Everyday script')
logger.warning('Warning Started Everyday script')
logger.critical('Critical Started Everyday script')