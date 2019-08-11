# -*- coding: utf-8 -*-
# Author: Chery-Huo
from django import views
from iworkflow import models as w_model
from django.shortcuts import HttpResponse
from rest_framework.response import Response

#
# def get_status(request):
#     """
#     获取当前流程实例状态,获取吓一跳内容
#         :param request:
#         :return:
#     """
#
#     if request.method == "GET":
#         p_obj = w_model.TaskInstance.objects.all().first()
#         print p_obj
#         return HttpResponse('123123123')
