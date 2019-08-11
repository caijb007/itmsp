# coding: utf-8
# Author: Chery-Huo


#
# def post_data_to_dict(data):
#     """
#     将request.data类型统一为dict
#     """
#     if isinstance(data, QueryDict):
#         return data.dict()
#     elif isinstance(data, DataAndFiles):
#         return data.data.dict()
#     elif isinstance(data, dict):
#         return data
#     else:
#         raise Exception(u"POST传入参数须为json格式")