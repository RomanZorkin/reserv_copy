import logging

from service.config import load_from_yaml
from service.worker import backup

logger = logging.getLogger(__name__)
config = load_from_yaml()


def run():
    logger.debug('start run fun')
    backup.run(config)
