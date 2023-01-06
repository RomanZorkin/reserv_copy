import logging

from service import app

logging.basicConfig(level=logging.WARNING)

if __name__ == '__main__':
    app.run()
