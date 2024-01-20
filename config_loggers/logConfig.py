import logging
from pathlib import Path


def setup_logger():
    logger = logging.getLogger("my_app_logger")
    logger.setLevel(logging.DEBUG)
    cur: Path = Path(__file__).parent.parent

    # Create a file handler and set the formatter
    log_file = cur / "logs/app_log.txt"
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Create a filter to exclude traceback information for INFO and WARNING levels
    no_traceback_filter = NoTracebackFilter()

    # Apply the filter to the file handler
    file_handler.addFilter(no_traceback_filter)

    logger.addHandler(file_handler)

    return logger


class NoTracebackFilter(logging.Filter):
    def filter(self, record):
        # Exclude traceback information for INFO and WARNING levels
        return record.levelno not in [logging.INFO, logging.WARNING]
