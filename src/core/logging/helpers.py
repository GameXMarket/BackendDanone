import logging
import colorlog


def create_logger(base_logger_name, base_logger_level=logging.INFO):
    logger = logging.getLogger(base_logger_name)
    logger.setLevel(base_logger_level)

    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s%(reset)s:\t\t%(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger
