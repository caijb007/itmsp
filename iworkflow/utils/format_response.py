# coding: utf-8
# Author: Chery-Huo
# 用于格式化response


import json

from django.http import HttpResponse


def api_response(code, msg='', data=''):
    """
    用于一个格式化返回的方式
    :param code:
    :param msg: 信息
    :param data: 数据
    :return: http响应
    """

    return HttpResponse(json.dumps(dict(code=code, data=data, msg=msg)), content_type="application/json")
