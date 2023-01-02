import logging

from service import app

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    app.run()
