# coding: utf-8
# Author: Chery-Huo
def return_dict_value(key):
    """

    :param key:
    :return:
    """
    ServerAndProcessDict = {
        "vmwarebase_resource_supply": "/ivmware/vmgenerate-approve/"
    }
    if not key:
        return {'status': -1, 'msg': "没有KEY", 'data': []}

    you_are_right_key = ServerAndProcessDict.get(key)
    return you_are_right_key
