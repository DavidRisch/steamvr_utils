import logging
import sys
import os

d = logging.debug
i = logging.info
w = logging.warning
e = logging.error


def initialise(config):
    log_formatter = logging.Formatter('%(asctime)19.19s [%(levelname)-5.5s]: %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(config.log_path())
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    symlink_path = os.path.join(os.path.dirname(config.log_path()), 'latest.log')
    if os.path.isfile(symlink_path):
        os.unlink(symlink_path)
    os.symlink(os.path.basename(config.log_path()), symlink_path)

