# coding: utf-8
# Author: Dunkle Qiu

from django.db.models import Q
from traceback import format_exc
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import APIException, PermissionDenied

from iuser.permissions import *
from itmsp.utils.decorators import post_validated_fields, status, post_data_to_dict
from itmsp.utils.base import logger, smart_get
from itmsp.utils.ssh import toString_PUTTY_private, get_rsakey_from_string
from . import serializers
from .utils import *

from rest_framework import viewsets


class ExUserViewSet(viewsets.ModelViewSet):
    """
    用户操作
    """
    queryset = ExUser.objects.all()
    serializer_class = serializers.ExUserSerializerSet


class ExGroupsViewSet(viewsets.ModelViewSet):
    """
    用户组操作
    """
    queryset = ExGroup.objects.all()
    serializer_class = serializers.ExGroupSerializerSet


@api_view(['POST'])
# @permission_classes((require_menu(["I00201"]),))
@post_validated_fields(require=['username', 'email', 'password', 'group_id'])
def user_add(request):
    """
    添加用户

    * 参数
    ** username - 用户名称
    ** email - 邮箱地址
    ** password - 密码
    ** aam_id - 统一认证号
    ** name - 显示名称
    ** group_id - 用户组id(','号分隔列表)
    ** role - 角色(CU/GM/SN), SU只通过后台创建
    """
    msg_prefix = u"添加用户 %s "
    req_dict = post_data_to_dict(request.data)

    username = smart_get(req_dict, 'username', str)
    email = smart_get(req_dict, 'email', str)
    password = smart_get(req_dict, 'password', str)

    aam_id = smart_get(req_dict, 'aam_id', str, '')
    group_id = smart_get(req_dict, 'group_id', list, default_list=None)
    name = smart_get(req_dict, 'name', unicode, '')
    role = smart_get(req_dict, 'role', str, 'CU')
    try:
        if ExUser.objects.filter(username=username):
            raise Exception(u'用户名已存在')
        user = ExUser.objects.create_user(username, email, password, name, role, aam_id=aam_id)
        user_gen_rsakey(user, key_expiration=timezone.now() + timezone.timedelta(days=ExUser.KEY_LIFE))
        user_id = user.id
        if group_id:
            for var in group_id:
                group = ExGroup.objects.get(pk=int(var))
                group_add_user(group, user_id)
        serializer = serializers.ExUserSerializer(user)
    except Exception, e:
        msg = (msg_prefix % username) + u"失败, 错误信息: " + unicode(e)
        logger.error(msg)
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = (msg_prefix % username) + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['GET', 'POST'])
# @permission_classes((require_menu(["I00201"]),))
def user_list(request):
    """
    获取用户列表

    * 参数
    ** search - 搜索匹配(用户名/显示名/邮箱)
    ** roles - 匹配角色(','号分隔列表)
    ** group_ids - 匹配用户组(','号分隔列表)
    """
    msg_prefix = u"获取用户列表 "
    try:
        users = ExUser.objects.all()
        if request.method == 'POST':
            req_dict = post_data_to_dict(request.data)

            keyword = smart_get(req_dict, 'search', unicode, '')
            roles = smart_get(req_dict, 'role', list)
            groups = smart_get(req_dict, 'group_ids', list)
            if keyword:
                users = users.filter(
                    Q(username__icontains=keyword) | Q(name__icontains=keyword) | Q(email__icontains=keyword))
            if roles:
                users = users.filter(role__in=roles)
            if groups:
                users = users.filter(groups__in=groups)
        serializer = serializers.ExUserSerializer(users, many=True)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(msg)
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": serializer.data})


@api_view(['GET', 'POST'])
# @permission_classes((require_menu(["I00201", "I00203"]),))
def user_detail(request):
    """
    获取用户详情

    * 参数
    ** id - 用户id
    """
    msg_prefix = u"获取用户详情 "
    req_user = request.user
    try:
        if request.method == 'GET':
            user = req_user
        else:
            req_dict = post_data_to_dict(request.data)

            id = smart_get(req_dict, 'id', int)
            user = ExUser.objects.get(pk=int(id))
        serializer = serializers.ExUserDetailSerializer(user)
    except Exception, e:
        if isinstance(e, APIException):
            raise e
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(msg)
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": serializer.data})


@api_view(['POST'])
@post_validated_fields(require=['id'])
# @permission_classes((require_menu(["I00201", "I00203"]),))
def user_edit(request):
    """
    修改用户信息

    * 参数
    ** id - 用户id
    ** email - 邮箱地址
    ** password - 密码
    ** name - 显示名称
    ** role - 角色(CU/GM/SN), SU只通过后台创建
    ** is_active - 激活状态
    ** aam_id - 统一认证号
    """
    msg_prefix = u"修改用户信息 ID:%s "
    req_dict = post_data_to_dict(request.data)
    req_user = request.user

    id = smart_get(req_dict, 'id', int)

    email = smart_get(req_dict, 'email', str, '')
    password = smart_get(req_dict, 'password', str, '')
    name = smart_get(req_dict, 'name', unicode, '')
    role = smart_get(req_dict, 'role', str, '')
    is_active = smart_get(req_dict, 'is_active', bool, True)
    aam_id = smart_get(req_dict, 'aam_id', str, '')

    try:
        user = ExUser.objects.get(pk=int(id))
        # 判定是否高权限调用
        lv_admin = "I00201" in get_menus(req_user)
        if not lv_admin and req_user != user:
            raise PermissionDenied()
        if email:
            user.email = email
        if role and lv_admin:
            user.role = role
            user.is_superuser = (role == 'SU')
            user.is_staff = (role == 'SU')
        if name:
            user.name = name
        if password:
            user.set_password(password)
        if aam_id:
            user.aam_id = aam_id
        # 防止admin被冻结
        if user.username == 'admin':
            is_active = True
        user.is_active = is_active
        user.save()
        serializer = serializers.ExUserDetailSerializer(user)
    except Exception, e:
        if isinstance(e, APIException):
            raise e
        msg = (msg_prefix % id) + u"失败, 错误信息: " + unicode(e)
        logger.error(msg)
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = (msg_prefix % id) + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
@post_validated_fields()
# @permission_classes((require_menu(["I00203"]),))
def user_mana_key(request):
    """
    管理用户RSA密钥

    * 参数
    ** generate - 生成新密钥
    ** download - 下载私钥
    ** passphrase - 私钥密码
    ** puttykey - putty格式
    """
    msg_prefix = u"管理用户RSA密钥 "
    req_dict = post_data_to_dict(request.data)
    user = request.user

    generate = smart_get(req_dict, 'generate', bool, False)
    download = smart_get(req_dict, 'download', bool, False)
    passphrase = smart_get(req_dict, 'passphrase', str, '')
    puttykey = smart_get(req_dict, 'puttykey', bool, False)

    try:
        # admin系统内置账户不可更换密钥
        if user.username == 'admin':
            generate = False
        if generate:
            user_gen_rsakey(user, key_expiration=timezone.now() + timezone.timedelta(days=ExUser.KEY_LIFE))
        if download:
            key = get_rsakey_from_string(user.ssh_key_str, passphrase=ExUser.KEY_PASSPHRASE)
            if puttykey:
                key_filename = "putty_pkey.ppk"
                key_string = toString_PUTTY_private(key, passphrase=passphrase)
            else:
                key_filename = "{username}.id_rsa".format(username=user.username)
                key_string = get_key_string(key, passphrase=passphrase)
            response = StreamingHttpResponse(content_type='application/octet-stream')
            response['Content-Disposition'] = "attachment; filename={filename}".format(filename=key_filename)
            response.streaming_content = key_string
            return response
    except Exception, e:
        if isinstance(e, APIException):
            raise e
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": {}})


# 功能已废弃
#
# @api_view(['POST'])
# @permission_classes((require_role(ROLES.SU[0]),))
# @post_validated_fields(require=['username', 'id'])
# def user_delete(request):
#     """
#     删除用户
#
#     * 权限 - 超级管理员(SU)
#     * 需同时提供用户名及id列表
#     * 参数
#     ** username - 用户名称(','号分隔列表)
#     ** id - 用户id(','号分隔列表)
#     """
#     msg_prefix = u"删除用户 "
#     req_dict = post_data_to_dict(request.data)
#     req_user = request.user
#     username = split(req_dict.pop('username'))
#     id = split(req_dict.pop('id'))
#     try:
#         user_set = ExUser.objects.filter(id__in=id).filter(username__in=username)
#         if not user_set.exists():
#             raise Exception(u"没有符合条件的用户")
#         if req_user in user_set:
#             raise Exception(u"不能删除当前用户!")
#         data = list(user_set.values('id', 'username', 'name', 'role'))
#         user_set.delete()
#     except Exception, e:
#         msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
#         logger.error(msg)
#         return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     else:
#         msg = msg_prefix + u"成功!"
#         return Response({"status": 1, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00202"]),))
@post_validated_fields(require=['name'])
def group_add(request):
    """
    添加用户组

    * 权限 - 超级管理员(SU)
    * 参数
    ** name - 用户组名称
    ** comment - 用户组描述
    ** users_id - 初始用户(id)(','号分隔列表)
    ** member_type - 成员类型 staff/service (默认staff)
    ** managers_id - 管理用户(id)(','号分隔列表)
    ** menu_list - 菜单权限清单,(','号分隔列表)
    """
    msg_prefix = u"添加用户组 %s "
    req_dict = post_data_to_dict(request.data)

    name = smart_get(req_dict, 'name', str)
    users_id = smart_get(req_dict, 'users_id', list)
    managers_id = smart_get(req_dict, 'managers_id', list)
    comment = smart_get(req_dict, 'comment', unicode, '')
    member_type = smart_get(req_dict, 'member_type', str, 'staff')
    menu_list = smart_get(req_dict, 'menu_list', list)

    try:
        if Group.objects.filter(name=name):
            raise Exception(u'组名已存在')
        group = ExGroup.objects.create(name=name, comment=comment, member_type=member_type, menu=menu_list)
        group_add_users(group, *users_id)
        group_add_manager(group, *managers_id)
        serializer = serializers.ExGroupSerializer(group)
    except Exception, e:
        msg = (msg_prefix % name) + u"失败, 错误信息: " + unicode(e)
        logger.error(msg)
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = (msg_prefix % name) + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['GET', 'POST'])
# @permission_classes((require_menu(["I00202"]),))
def group_list(request):
    """
    用户组列表

    * 权限 - 超级管理员(SU)
    * 参数
    ** search - 用户组名称
    ** type - 用户类型
    """
    msg_prefix = u"获取用户组列表 "
    try:
        groups = ExGroup.objects.all()
        if request.method == 'POST':
            req_dict = post_data_to_dict(request.data)

            keyword = smart_get(req_dict, 'search', unicode, '')
            member_type = smart_get(req_dict, 'type', str, '').lower()
            if keyword:
                groups = groups.filter(Q(name__icontains=keyword) | Q(comment__icontains=keyword))
            if member_type:
                groups = groups.filter(member_type=member_type)
        serializer = serializers.ExGroupSerializer(groups, many=True)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(msg)
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00202"]),))
@post_validated_fields(require=['id'])
def group_edit(request):
    """
    修改用户信息

    * 权限 - 普通用户(CU)
    * 参数
    ** id - 用户组id
    ** comment - 备注
    ** member_type - 成员类型 staff/service
    ** users_id/users_id_add - 用户/添加用户(id)(','号分隔列表)
    ** managers_id/managers_id_add - 管理用户/添加管理用户(id)(','号分隔列表)
    ** menu_list - 菜单权限清单/修改菜单权限清单(','号分隔列表)
    """

    msg_prefix = u"修改用户组信息 ID:%s "
    req_dict = post_data_to_dict(request.data)

    id = smart_get(req_dict, 'id', int)

    comment = smart_get(req_dict, 'comment', unicode, '')
    member_type = smart_get(req_dict, 'member_type', str, '')
    users_id = smart_get(req_dict, 'users_id', list, default_list=None)
    users_id_add = smart_get(req_dict, 'users_id_add', list)
    managers_id = smart_get(req_dict, 'managers_id', list, default_list=None)
    managers_id_add = smart_get(req_dict, 'managers_id_add', list)
    menu_list = smart_get(req_dict, 'menu_list', list, default_list=None)

    try:
        # 获取用户组
        group = ExGroup.objects.get(pk=int(id))
        # 修改信息
        if comment:
            group.comment = comment
        if member_type:
            group.member_type = member_type

        if users_id is not None:
            group.user_set.clear()
            users_id_add += users_id
        if users_id_add:
            group_add_users(group, *users_id_add)

        if managers_id is not None:
            group.managers.clear()
            managers_id_add += managers_id

        if menu_list is not None:
            group.menu = menu_list
            group.save()

        if managers_id_add:
            group_add_manager(group, *managers_id_add)

        serializer = serializers.ExGroupSerializer(group)
    except Exception, e:
        msg = (msg_prefix % id) + u"失败, 错误信息: " + unicode(e)
        logger.error(msg)
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = (msg_prefix % id) + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
@post_validated_fields(require=['id'])
# @permission_classes((require_menu(["I00202"]),))
def group_delete(request):
    """
    删除用户组

    * 权限 - 超级管理员(SU)
    * 参数
    ** id - 组id
    """
    msg_prefix = u"删除用户组 "
    req_dict = post_data_to_dict(request.data)

    id = smart_get(req_dict, 'id', int)
    try:
        # 获取用户组
        group_set = ExGroup.objects.filter(id=id)
        if not group_set.exists():
            raise Exception(u"没有符合条件的用户组")
        data = list(group_set.values('id', 'name', 'member_type'))
        group_set.delete()
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(msg)
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": data})
