from service.config import load_from_yaml
from service.worker import backup

config = load_from_yaml()


def run():
    print('start')
    backup.run(config)
    return None
