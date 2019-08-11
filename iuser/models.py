# coding: utf-8
# Author: Dunkle Qiu

from time import time
from django.contrib.auth.models import AbstractUser, Group
from django.db import models

from itmsp.utils.fields import JsonField
from itmsp.utils.base import ROLES
from itmsp.utils.ssh import get_rsakey_from_string, get_key_string, gen_rsakey
from iuser.managers import *


class ExGroup(Group):
    """
    自定义扩展组模型
    """
    MEM_TYPE_CHOICES = (
        ('staff', 'Staff'),
        ('service', 'Service'),
    )
    comment = models.CharField(max_length=160, blank=True, null=True)
    member_type = models.CharField(max_length=10, choices=MEM_TYPE_CHOICES, default='staff')
    managers = models.ManyToManyField('ExUser', related_name="mana_group_set", related_query_name="mana_group")
    # managers = models.ManyToManyField('ExUser', through="Membership")
    menu = JsonField(default=[])


class ExUser(AbstractUser):
    """
    自定义用户模型
    """
    # SSH RSA密钥常量
    KEY_PASSPHRASE = ''
    KEY_LIFE = 30

    name = models.CharField(max_length=80)
    role = models.CharField(max_length=2, choices=ROLES.as_choice(), default='CU')
    ssh_key_str = models.TextField(null=True)
    ssh_key_expiration = models.DateTimeField(null=True)
    ssh_key_birthday = models.BigIntegerField(default=0)
    aam_id = models.CharField(max_length=10, default='')

    objects = ExUserManager()

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.username

    def gen_key(self, bit=2048):
        new_key = gen_rsakey(bit)
        return new_key

    def set_key(self, key, key_expiration=None):
        key_string = get_key_string(key, passphrase=self.KEY_PASSPHRASE)
        self.ssh_key_str = key_string
        self.ssh_key_birthday = int(time())
        if key_expiration is not None:
            self.ssh_key_expiration = key_expiration
        self.save(update_fields=['ssh_key_str', 'ssh_key_expiration', 'ssh_key_birthday'])

    @property
    def ssh_pubkey_str(self):
        key = get_rsakey_from_string(self.ssh_key_str, passphrase=self.KEY_PASSPHRASE)
        return get_key_string(key, privatekey=False)

#
# class Membership(models.Model):
#     exuser = models.ForeignKey(ExUser, on_delete=models.CASCADE)
#     exgroup = models.ForeignKey(ExGroup, on_delete=models.CASCADE)

#
# class UserSSHAuth(models.Model):
#     """
#     用户SSH权限表
#     """
#     NORMAL = 'normal'
#     INVALID = 'invalid'
#     FROZEN = 'frozen'
#     REPLACED = 'replaced'
#     ST_CHOICE = (
#         (NORMAL, u"正常"),
#         (INVALID, u"失效"),
#         (FROZEN, u"已冻结"),
#         (REPLACED, u"已更换"),
#     )
#     user = models.ForeignKey('ExUser', to_field='username', )
#     remote_host = models.CharField(max_length=30)
#     remote_user = models.CharField(max_length=30)
#     auth_key = models.TextField(null=True)
#     auth_status = models.CharField(max_length=30, default=NORMAL, choices=ST_CHOICE)
#     auth_bgn_date = models.DateTimeField(null=True)
#     auth_end_date = models.DateTimeField(null=True)
