import logging

logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s'
)

ilogger = logging.getLogger('integration_utils')