# coding: utf-8
# Author: Dunkle Qiu

from itmsp.managers import *
from itmsp.utils.fields import JsonField
from django.utils.timezone import now


# from .urls import get_all_url


class DataDict(models.Model):
    """
    应用参数及动态表单选项
    """
    CH_SETTING_TYPE = (
        ('PARAM', 'parameter'),
        ('OPTION', 'field options')
    )
    app = models.CharField(max_length=20)
    setting_type = models.CharField(max_length=20, choices=CH_SETTING_TYPE)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    display = models.CharField(max_length=255, null=True)
    ext_attr = JsonField(default={})

    objects = models.Manager()
    params = ParamManager()
    options = OptionManager()

    class Meta:
        unique_together = ('app', 'setting_type', 'name', 'value')

    def __unicode__(self):
        return "_%s_%s_%s" % (self.app, self.setting_type, self.name)


class System(models.Model):
    """
    应用系统表
    """
    name = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    primary_dev = models.CharField(max_length=100, null=True)
    other_dev = JsonField(default=[])
    primary_op = models.CharField(max_length=100, null=True)
    other_op = JsonField(default=[])
    app_level = models.CharField(max_length=20, default='')
    dr_level = models.CharField(max_length=20, default='')
    topo_graph = models.TextField(null=True)


class J2TemplFile(models.Model):
    """
    Jinja2模板实例表
    """
    src = models.CharField(max_length=100)
    dest = models.CharField(max_length=100)
    host = models.CharField(max_length=20)
    owner = models.CharField(max_length=20, null=True)
    group = models.CharField(max_length=20, null=True)
    mode = models.CharField(max_length=20, null=True)
    var_dict = JsonField(default={})

    @property
    def file_attr(self):
        dc = dict()
        if self.owner:
            dc['owner'] = self.owner
        if self.group:
            dc['group'] = self.group
        if self.mode:
            dc['mode'] = self.mode
        return dc
