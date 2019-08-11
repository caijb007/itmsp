# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from itmsp.utils.fields import JsonField
from iuser.models import ExUser
from django.utils.translation import ugettext_lazy as _

DEFAULT_CATEGORY = "默认分组"

COMPONENT_TYPE = {
    (0, '接口'),
    (1, '参数'),
    (2, '模块'),
    (3, '蓝图'),
}

DATA_TYPE = {
    ('str', "字符串"),
    ('list', "数组"),
    ('int', "整数"),
    ('bool', "布尔数")
}
STREAM_TYPE = {
    ('input', "输入"),
    ('output', "输出")
}


################################################################
#########################蓝图定义设计表###########################
################################################################
# Create your models here.
class BlueComponentDefinition(models.Model):
    """
    蓝图组件库定义表
    """
    component_category = models.CharField(max_length=64)
    component_type = models.SmallIntegerField(choices=COMPONENT_TYPE)
    component_entity = models.IntegerField()


class BlueComponentCategory(models.Model):
    """
    蓝图组件实体分组表
    """
    description = models.CharField(max_length=255, default=None, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(null=True, auto_now=True)


class BlueInterfaceCategory(BlueComponentCategory):
    """
    蓝图接口组件实体分组表
    """
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=64, default='#6C5CE7')

    def __str__(self):
        return self.name


class BluePreParamGroupCategory(BlueComponentCategory):
    """
    蓝图预定义参数组组件实体分组表
    """
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=64, default='#FFD')

    def __str__(self):
        return self.name


class BlueAccessModuleParamGroupCategory(BlueComponentCategory):
    """
    蓝图接入模块参数组组件实体分组表
    """
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=64, default='#F0D')

    def __str__(self):
        return self.name


class BlueCategory(BlueComponentCategory):
    """
    蓝图组件实体分组表
    """
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=64, default='#6C5444')

    def __str__(self):
        return self.name


class BlueComponentEntityDefinition(models.Model):
    """
    蓝图组件实体定义公共字段表
    """
    name = models.CharField(max_length=100, default=None)
    description = models.CharField(max_length=255, null=True)
    is_freeze = models.BooleanField(default=False)
    is_component = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(null=True, auto_now=True)

    def __str__(self):
        return self.name


class BlueComponentEntityParam(models.Model):
    """
    蓝图组件实体参数公共字段
    """
    param_name = models.CharField(max_length=100)
    data_type = models.CharField(choices=DATA_TYPE, max_length=100, default='str')
    description = models.CharField(max_length=30, default=None)


class BlueInterfaceDefinition(BlueComponentEntityDefinition):
    """
    蓝图接口表
    """
    category = models.ForeignKey(to=BlueInterfaceCategory, null=True, on_delete=models.SET_NULL)
    func_name = models.CharField(max_length=100)
    url = models.CharField(max_length=255, unique=True)


class BlueInterfaceParam(BlueComponentEntityParam):
    """
    蓝图接口参数表
    """
    blue_interface = models.ForeignKey(to=BlueInterfaceDefinition, related_name="params")
    require = models.BooleanField(default=True)
    io_stream = models.CharField(choices=STREAM_TYPE, max_length=100, default='input')


class BluePreParamGroup(BlueComponentEntityDefinition):
    """
    蓝图预定义参数组表
    """
    category = models.ForeignKey(to=BluePreParamGroupCategory, null=True, on_delete=models.SET_NULL)


class BluePreParamGroupParam(BlueComponentEntityParam):
    """
    蓝图预定义参数组参数表
    """
    blue_pre_param_group = models.ForeignKey(to=BluePreParamGroup, related_name="params")
    value = models.CharField(max_length=100)


class BlueAccessModuleParamGroup(BlueComponentEntityDefinition):
    """
    蓝图接入模块参数组表
    """
    category = models.ForeignKey(to=BlueAccessModuleParamGroupCategory, null=True, on_delete=models.SET_NULL)
    access_module_key = models.CharField(max_length=255)


class BlueAccessModuleParamsGroupParam(BlueComponentEntityParam):
    """
    蓝图接入模块参数组参数表
    """
    blue_access_module_group = models.ForeignKey(to=BlueAccessModuleParamGroup, related_name="params")


class BluePrintDefinition(BlueComponentEntityDefinition):
    """
    蓝图定义表
    """
    KEEP_STATUS = {
        (0, _('草稿')),  # 初始状态
        (1, _('已保存')),  # 保存蓝图后状态
    }
    VALID_STATUS = {
        (0, _('未验证')),
        (1, _('蓝图有效')),
        (2, _('蓝图无效'))
    }
    category = models.ForeignKey(BlueCategory, null=True, on_delete=models.SET_NULL)
    is_valid = models.SmallIntegerField(choices=VALID_STATUS, default=0, null=True)  # 手工维护
    created_user = models.ForeignKey(ExUser, on_delete=models.SET_NULL, null=True)
    tmp = models.IntegerField(null=True, default=None)
    keep_status = models.SmallIntegerField(choices=KEEP_STATUS, default=0)
    input = JsonField(default={})
    output = JsonField(default={})
    is_verify = models.BooleanField(default=False)  # 验证节点参数
    link_data = JsonField(default={})
    avaliable_node_sort = JsonField(default=[])  # 节点执行顺序

    def __str__(self):
        return self.name


class BlueNodeDefinition(models.Model):
    """
    蓝图节点表(接口)
    """
    blue_print = models.ForeignKey(BluePrintDefinition, related_name="blue_nodes")
    name = models.CharField(max_length=100, default=None)  # 填写接口name
    key = models.CharField(max_length=10, default=None, null=True)  # 前段需要显示字段， 保存当前id
    is_verify = models.BooleanField(default=False)  # 验证节点参数
    is_maintain = models.BooleanField(default=False)  # 是否维护中
    component_type = models.SmallIntegerField(choices=COMPONENT_TYPE, default=0)  # 组件类型
    component_data = JsonField(default={})
    downstream_node = models.ManyToManyField("BlueNodeDefinition", related_name="down_nodes", blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(null=True, auto_now=True)

    def __str__(self):
        return self.name


class BlueNodeMapParam(models.Model):
    """
    蓝图节点和参数映射
    """
    blue_print = models.ForeignKey(BluePrintDefinition)
    target_node = models.IntegerField()
    target_param_name = models.CharField(max_length=64)
    source_node = models.IntegerField()
    source_param_name = models.CharField(max_length=64)


################################################################
#########################蓝图引擎设计表###########################
################################################################
class BlueInstance(models.Model):
    """
    蓝图实例表
    """
    STATUS = [
        (0, _('开始')),
        (1, _('运行中')),
        (2, _('已完成')),
        (3, _('异常')),
    ]
    blue_instance_number = models.CharField(u"蓝图实例编号", unique=True, max_length=255, null=True, blank=True)
    blue_print = models.ForeignKey(BluePrintDefinition, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(ExUser, null=True, on_delete=models.SET_NULL)  # 申请人
    status = models.SmallIntegerField(choices=STATUS, default=0)
    avaliable_node_sort = JsonField(default=[])  # 节点执行顺序
    startTime = models.DateTimeField(auto_now_add=True)
    endTime = models.DateTimeField(null=True, blank=True)
    current_node = models.ForeignKey(BlueNodeDefinition, null=True, on_delete=models.SET_NULL, default=None)


class NodeInstance(models.Model):
    """
    节点任务实例
    """
    STATUS = [
        (0, _('开始')),
        (1, _('参数赋值')),
        (2, _('开始执行')),
        (3, _('执行完毕')),
        (4, _('输出参数回填')),
        (5, _('结束')),
        (6, _('异常')),
    ]
    node_instance_name = models.CharField(u"节点实例名称", max_length=255, null=True, blank=True)
    blue_instance = models.ForeignKey(BlueInstance, related_name='node_instance', null=True, on_delete=models.SET_NULL)
    node_input_entrance = JsonField(u"节点输入口", default={})
    blue_node = models.ForeignKey(BlueNodeDefinition, null=True, on_delete=models.SET_NULL)
    status = models.SmallIntegerField(choices=STATUS, default=0)
    node_returns = JsonField(default={})
    url = models.CharField(max_length=255, null=True, blank=True)
    startTime = models.DateTimeField(auto_now_add=True)
    endTime = models.DateTimeField(null=True, blank=True)


class BlueAccessModuleParamsInstance(models.Model):
    access_module_key = models.CharField(_("接入模块KEY"), max_length=255, null=True, blank=True)
    blue_print = models.SmallIntegerField(_("蓝图定义"), null=True, blank=True)
    blue_instance_number = models.CharField(_("蓝图实例编号"), max_length=255, null=True, blank=True)
    user = models.ForeignKey(to=ExUser, null=True, blank=True, on_delete=models.SET_NULL)
    business_data = JsonField(_("业务数据"), default={})
    startTime = models.DateTimeField(auto_now_add=True)


class BlueEngineTask(models.Model):
    blue_instance_number = models.CharField(_("蓝图实例编号"), max_length=255, null=True, blank=True)
    blue_engine_log = models.TextField()
    access_module_key = models.CharField(_("接入模块KEY"), max_length=255, null=True, blank=True)
    blue_print_id = models.SmallIntegerField(_("蓝图定义"), null=True, blank=True)
    user = models.ForeignKey(to=ExUser, null=True, blank=True, on_delete=models.SET_NULL)
    task_progress = models.CharField(_("进度"), max_length=64, null=True, blank=True)
    result_data = JsonField(default={})
    startTime = models.DateTimeField(auto_now_add=True)
    task_elapsed_time = models.CharField(_("任务耗时"), max_length=64, null=True, blank=True)
