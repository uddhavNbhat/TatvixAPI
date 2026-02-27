import logging

class Logger:
    _instance = None

    def __init__(self):
        self.logger = logging.getLogger("app")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="{asctime} - {levelname} - {message}",
                style="{",
                datefmt="%Y-%m-%d %H:%M",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    @classmethod
    def get_logger(cls):
        """ Decoupled creation method to return logger singleton """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance.logger

# Default instance to use
logger = Logger.get_logger()