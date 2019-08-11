# coding: utf-8
# Author: Chery-Huo
import functools
# import logging
import traceback

# logger = logging.getLogger('django')


def auto_log(func):
    """
    这是一个自动记录日志的装饰器
    :param func:
    :return:
    """

    @functools.wraps(func)
    def _inner(*args, **kwargs):
        try:
            real_func = func(*args, **kwargs)
            return real_func
        except Exception as e:
            logger.error(traceback.format_exc())
            return False, e.__str__()

    return _inner
