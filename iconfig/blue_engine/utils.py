import os
import logging
from itmsp.settings import LOG_DIR, LOG_LEVEL
def set_log(level, filename='blue_engine.log', logger_name='blue_engine'):
    """

    :param level:
    :param filename:
    :param logger_name:
    :return:
    """
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_file = os.path.join(LOG_DIR, filename)
    if not os.path.isfile(log_file):
        os.mknod(log_file)
        os.chmod(log_file, 0644)
    log_level_total = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARN, 'error': logging.ERROR,
                       'critical': logging.CRITICAL}
    logger_f = logging.getLogger(logger_name)
    logger_f.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    fh.setLevel(log_level_total.get(level, logging.DEBUG))
    formatter = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger_f.addHandler(fh)

    return logger_f


