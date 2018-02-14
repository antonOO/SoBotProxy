import logging
import os.path

def initialize_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
