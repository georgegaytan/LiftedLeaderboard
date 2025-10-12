import logging
import sys


def setup_logging(level: int = logging.INFO):
    '''Configure root logger for the entire codebase.'''
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],  # logs to console
    )
