import logging
from pathlib import Path


def setup_logger():
    logger = logging.getLogger("my_app_logger")
    logger.setLevel(logging.DEBUG)
    cur = Path(__file__).parent.parent

    # Create a file handler and set the formatter
    log_file = cur / "logs/app_log.txt"
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Apply the formatter to the file handler
    logger.addHandler(file_handler)

    return logger