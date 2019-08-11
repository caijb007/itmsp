# coding: utf-8
# Author: Dunkle Qiu

from django.utils import timezone

from itmsp.utils.base import logger
from itmsp.utils.ssh import gen_rsakey, get_key_string

from .models import ExUser, ExGroup


def group_add_users(group, *user_id):
    """
    用户组中添加用户
    """
    count = 0
    for val in user_id:
        if isinstance(val, int):
            user = ExUser.objects.filter(pk=val)
        elif val:
            user = ExUser.objects.filter(pk=int(val))
        else:
            continue
        if user.exists():
            group.user_set.add(user[0])
        count += 1
    return count


def group_add_user(group, user_id):
    """
    用户组中添加用户
    """
    count = 0
    user = ExUser.objects.filter(pk=int(user_id))
    if user.exists():
        group.user_set.add(user[0])
        count += 1
    return count


def group_add_manager(group, *user_id):
    """
    用户组中添加组管理员
    """
    count = 0
    if not isinstance(group, ExGroup):
        raise TypeError("group must be ExGroup")
    for val in user_id:
        if isinstance(val, int):
            user = ExUser.objects.filter(pk=val)
        elif val:
            user = ExUser.objects.filter(pk=int(val))
        else:
            continue
        if user.exists():
            group.managers.add(user[0])
        count += 1
    return count


def user_gen_rsakey(user, bit=2048, key_expiration=None):
    """
    为用户生成SSH Key
    """
    if not isinstance(user, ExUser):
        raise TypeError("user must be ExUser")
    new_key = gen_rsakey(bit)
    user.set_key(new_key, key_expiration=key_expiration)
