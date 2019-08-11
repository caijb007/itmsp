import logging
import collections


class TailLogHandler(logging.Handler):
    def __init__(self, log_queue):
        logging.Handler.__init__(self)
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.append(self.format(record))


class TailLogger(object):

    def __init__(self, maxlen):
        self._log_queue = collections.deque(maxlen=maxlen)
        self._log_handler = TailLogHandler(self._log_queue)

    def contents(self):
        return '~'.join(self._log_queue)

    @property
    def log_handler(self):
       return self._log_handler


# log_level_total = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARN, 'error': logging.ERROR,
#                        'critical': logging.CRITICAL}
blue_engine_task_logger = logging.getLogger(__name__)
tail = TailLogger(10)
formatter = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s')


log_handler = tail.log_handler
log_handler.setFormatter(formatter)
blue_engine_task_logger.addHandler(log_handler)
blue_engine_task_logger.setLevel(logging.DEBUG)
