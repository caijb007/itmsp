# coding: utf-8
# Author: Dunkle Qiu

from .models import Group, ROLES, ExGroup
from rest_framework import permissions
from itmsp.utils.base import logger, all_in


def require_role(role=ROLES.CU[0]):
    """
    验证用户是某种角色 ['SU','GM','CU','SN']的函数
    """

    class RoleAuthenticated(permissions.IsAuthenticated):
        message = "Permission denied, role of %s or above is required" % role

        def has_permission(self, request, view):
            is_auth = super(RoleAuthenticated, self).has_permission(request, view)
            if not is_auth:
                return False
            user_role = request.user.role
            if user_role == 'SU':
                return True
            elif role in ['SN', 'GM']:
                return user_role == role
            elif role == 'CU':
                return user_role in ['GM', 'CU']
            else:
                return False

    return RoleAuthenticated


def require_groups(groups=None):
    """
    验证用户属于某个群组
    """
    if not groups:
        return permissions.IsAuthenticated
    if isinstance(groups, str):
        groups = [groups]
    assert type(groups) in (tuple, list), "Type Error: groups must be a tuple or a list."

    class GroupAuthenticated(permissions.IsAuthenticated):
        message = "Permission denied, only members in \"%s\" is permitted" % ("".join(groups))

        def has_permission(self, request, view):
            is_auth = super(GroupAuthenticated, self).has_permission(request, view)
            if not is_auth:
                return False
            group_set = Group.objects.filter(name__in=groups)
            if group_set.exists():
                for group in request.user.groups.all():
                    if group in group_set:
                        return True
                return False
            else:
                return False

    return GroupAuthenticated


def get_menus(user):
    menus = set()
    for gr in user.groups.all():
        menu = gr.exgroup.menu
        menus.update(menu)
    return list(menus)


def get_users_by_memus(menus, only=True):
    groups = ExGroup.objects.all()
    user_list = []
    for group in groups:
        if only:
            if all_in(menus, group.menu):
                user_list = list(set(user_list).union(set(group.user_set.all())))
        else:
            for menu in menus:
                if menu in group.menu:
                    user_list = list(set(user_list).union(set(group.user_set.all())))
                    continue
    return user_list


def require_menu(menus):
    """
    验证用户是否有该接口调用权限的函数
    """
    class InterfacesAuthenticated(permissions.IsAuthenticated):
        def has_permission(self, request, view):
            is_auth = super(InterfacesAuthenticated, self).has_permission(request, view)
            if not is_auth:
                return False
            menu_list = get_menus(request.user)
            for menu in menus:
                if menu in menu_list:
                    return True
            return False

        message = "Permission denied, menu of %s or above is required" % menus
    return InterfacesAuthenticated
