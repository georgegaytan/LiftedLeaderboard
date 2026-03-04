import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(level: int = logging.INFO):
    '''Configure root logger for the entire codebase.'''
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logging.basicConfig(
        level=level,
        handlers=[stream_handler],  # logs to console
        force=True,  # Ensure no other handlers hijack
    )
