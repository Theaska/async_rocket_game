import logging


class FileLogger:
    def __init__(
        self,
        name: str,
        filename: str,
        mode: str = 'w',
        level: int = logging.INFO,
        formatter: str = "%(name)s %(asctime)s %(levelname)s %(message)s"
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        file_handler = logging.FileHandler(filename, mode=mode)
        formatter = logging.Formatter(formatter)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger