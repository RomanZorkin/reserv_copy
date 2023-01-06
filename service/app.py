import logging
from datetime import datetime

from service.config import load_from_yaml
from service.worker import backup

logger = logging.getLogger(__name__)
config = load_from_yaml()
start = datetime.now()

def run():
    logger.debug('start run fun')
    backup.run(config)
    finish = datetime.now()
    long = finish - start
    print(long)
