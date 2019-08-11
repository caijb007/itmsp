# coding: utf-8
# Author: Dunkle Qiu

from traceback import format_exc
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.views import Token, ObtainAuthToken
from rest_framework.decorators import action
from iuser.permissions import *
from itmsp.utils.decorators import post_validated_fields, status, post_data_to_dict
from itmsp.utils.base import logger, split
from itmsp import settings
from .authentication import obtain_token
from . import serializers
from .models import *
from rest_framework.viewsets import ModelViewSet


class ObtainExAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = obtain_token(user)
        menu_list = []
        for gr in user.groups.all():
            menu = gr.exgroup.menu
            menu_list = list(set(menu_list).union(set(menu)))

        return Response({"status": 0, "username": user.username, "displayname": user.name, 'token': token.key,
                         'role': user.role, "groups": [group.name for group in user.groups.all()], "menu": menu_list})


class OptionViewSet(ModelViewSet):
    """
    参数列表
    """
    queryset = DataDict.objects.all()
    serializer_class = serializers.DataDictSerializer


@api_view(['POST'])
@post_validated_fields(require=['app', 'name'], illegal=['options', 'value', 'display'])
def option_list(request):
    """
    获取动态表单选项

    * 权限 - 任何人
    * 参数
    ** app - 模块名称
    ** name - 表单名称
    ** 其他 - 其他附加属性
    """
    msg_prefix = u"获取表单选项 <%s> "
    req_dict = post_data_to_dict(request.data)

    app = req_dict.pop('app')
    name = req_dict.pop('name')
    try:
        data = DataDict.options.get_options_serialized(app, name, **req_dict)
    except Exception, e:
        msg = (msg_prefix % name) + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = (msg_prefix % name) + u"成功!"
        return Response({"status": 0, "msg": msg, "data": data})


@api_view(['GET', 'POST'])
def option_apps(request):
    """
    获取动态参数APP列表
    返回：
    app列表
    """
    msg_prefix = u"获取动态参数APP列表 "
    try:
        apps = DataDict.options.get_app()
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": apps})


@api_view(['POST'])
@post_validated_fields(require=['app'], )
def option_names(request):
    """
    根据应用名获取表单名
    """
    msg_prefix = u"获取表单名列表 "
    req_dict = post_data_to_dict(request.data)

    app = req_dict.pop('app')
    try:
        names = DataDict.options.get_name(app=app)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": names})


@api_view(['POST'])
@post_validated_fields(require=['app', 'name', 'value'], illegal=['options'])
def option_add(request):
    """
    添加动态表单选项

    * 权限 - 超级管理员(SU)
    * 参数
    ** app - 模块名称
    ** name - 表单名称
    ** value - 选项值
    ** display - 选项显示名称
    ** 其他 - 其他附加属性
    """
    msg_prefix = u"添加表单选项 <%s>:<%s> "
    req_dict = post_data_to_dict(request.data)

    app = req_dict.pop('app')
    name = req_dict.pop('name')
    value = req_dict.pop('value')
    display = req_dict.pop('display', '')
    try:
        created = DataDict.options.add_option(app, name, value, display, **req_dict)
        data = DataDict.options.get_options_serialized(app, name)
    except Exception, e:
        msg = (msg_prefix % (name, value)) + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = (msg_prefix % (name, value)) + (created and u"成功!" or u"失败, 该选项已存在!")
        return Response({"status": int(created), "msg": msg, "data": data})


@api_view(['POST'])
@post_validated_fields(require=['app', 'name', 'value'], illegal=['options'])
def option_edit(request):
    """
    修改动态表单选项

    * 权限 - 超级管理员(SU)
    * 参数
    ** app - 模块名称
    ** name - 表单名称
    ** value - 选项值
    ** display - 选项显示名称
    ** 其他 - 其他附加属性
    """
    msg_prefix = u"修改表单选项 <%s>:<%s> "
    req_dict = post_data_to_dict(request.data)

    app = req_dict.pop('app')
    name = req_dict.pop('name')
    value = req_dict.pop('value')
    display = req_dict.pop('display', '')
    try:
        updated = DataDict.options.update_option(app, name, value, display, **req_dict)
        data = DataDict.options.get_options_serialized(app, name)
    except Exception, e:
        msg = (msg_prefix % (name, value)) + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = (msg_prefix % (name, value)) + (updated and u"成功!" or u"失败, 没有匹配的条目!")
        return Response({"status": int(updated), "msg": msg, "data": data})


@api_view(['POST'])
@post_validated_fields(require=['app', 'name', 'value'])
def option_delete(request):
    """
    删除动态表单选项

    * 权限 - 超级管理员(SU)
    * 参数
    ** app - 模块名称
    ** name - 表单名称
    ** value - 选项值(','号分隔列表)
    """
    msg_prefix = u"删除表单选项 <%s>:<%s> "
    req_dict = post_data_to_dict(request.data)

    app = req_dict.pop('app')
    name = req_dict.pop('name')
    value = split(req_dict.pop('value'), ',')
    try:
        deleted = DataDict.options.delete_options(app, name, *value)
        data = DataDict.options.get_options_serialized(app, name)
    except Exception, e:
        msg = (msg_prefix % (name, ','.join(value))) + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = (msg_prefix % (name, ','.join(value))) + (deleted and u"成功!" or u"失败, 没有匹配的条目!")
        return Response({"status": deleted, "msg": msg, "data": data})
