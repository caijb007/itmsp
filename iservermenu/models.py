# -*- coding: utf-8 -*-
# Author: ld & Chery Huo
from __future__ import unicode_literals

from django.db import models
from iuser.models import ExGroup
from iconfig.models import BluePrintDefinition
from iworkflow.models import ProcessDefinition
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from itmsp.utils.fields import JsonField

IMPLEMENT = (
    (0, "蓝图"),
    (1, "流程")
)


# Create your models here.
class ServerMenuBase(models.Model):
    """
    服务目录基础表
    """
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True)
    coding = models.CharField(max_length=10, null=True, blank=True)  # 适用id在1000以下的场景
    on_delete = models.BooleanField(default=False, help_text="默认不删除,用于逻辑删除")

    class Meta:
        abstract = True


@python_2_unicode_compatible
class ServerMenuCategory(ServerMenuBase):
    """
    服务目录分类表
    """
    groups = models.ManyToManyField(ExGroup, blank=True)
    icon = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Servers(ServerMenuBase):
    """
    服务表
    """
    category = models.ForeignKey(ServerMenuCategory, null=True, on_delete=models.SET_NULL)
    groups = models.ManyToManyField(ExGroup, blank=True)
    is_freeze = models.BooleanField(default=False)
    implement = models.SmallIntegerField(choices=IMPLEMENT, default=0)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Pages(ServerMenuBase):
    """
    页面表
    """
    server = models.ForeignKey(Servers)
    page_type = models.SmallIntegerField(choices=IMPLEMENT, default=1)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Button(ServerMenuBase):
    """
    按钮表
    """
    page = models.ForeignKey(Pages, related_name='button')
    composite_code = models.CharField(verbose_name="综合编码", max_length=100, help_text="用于查询", null=True, blank=True)
    button_type = models.SmallIntegerField(choices=IMPLEMENT, default=0)

    def __str__(self):
        return self.name


class MapBase(models.Model):
    """
    映射表基础表
    """
    category_code = models.CharField(max_length=100)
    server_code = models.CharField(max_length=100)
    page_code = models.CharField(max_length=100)
    button_code = models.CharField(max_length=100)


class ServerMapWf(models.Model):
    """
    服务流程映射表
    """
    work_flow_key = models.CharField(max_length=100)
    node_id = models.SmallIntegerField(null=True, blank=True)
    # node_name = models.CharField(max_length=100, null=True, blank=True)
    synthesize_code = models.CharField(max_length=100, null=True, blank=True)
    parent_id = models.SmallIntegerField(_("父级节点"), null=True, blank=True)

    server_id = models.CharField(max_length=100, null=True, blank=True)
    # server_name = models.CharField(max_length=100, null=True, blank=True)
    page_id = models.SmallIntegerField(null=True, blank=True)
    # page_name = models.CharField(max_length=100, null=True, blank=True)

    # is_approve = models.BooleanField(default=False)


class ServerMapBp(models.Model):
    """
    服务蓝图映射表
    """
    blue_print_id = models.SmallIntegerField(_("蓝图ID"))
    # blue_print_name = models.CharField(max_length=64, null=True, blank=True)
    button_id = models.SmallIntegerField(_("按钮ID"))
    # button_name = models.CharField(_("按钮名称"), max_length=64, null=True, blank=True)
    synthesize_code = models.CharField(max_length=100, null=True, blank=True)


@python_2_unicode_compatible
class ServerParamsMG(models.Model):
    CH_SETTING_TYPE = (
        ('SELECT', '下拉参数'),
        ('INPUT', '输入参数')
    )
    server_id = models.SmallIntegerField(verbose_name=_("所属服务"))
    params_type = models.CharField(_("参数类型"), max_length=64, choices=CH_SETTING_TYPE)

    params_name = models.CharField(_("参数简称"), max_length=64, help_text="英文，与页面名称保持一致")
    parent_id = models.SmallIntegerField(_('父级ID'), help_text='用于区分级别', null=True, blank=True)
    params_name_display = models.CharField(_("参数名称"), max_length=255, help_text="中文，与页面名称保持一致",
                                           null=True, blank=True)
    values_en = models.CharField(_("参数值"), max_length=100, help_text="英文标识符，不可修改", null=True, blank=True)
    values_display = models.CharField(_("显示值"), max_length=255, help_text="中文，可修改", null=True, blank=True)
    param_option = JsonField(_("参数额外字段"), default={})
    param_comment = models.TextField(_("参数注释"), null=True, blank=True)
    is_editable = models.BooleanField(default=True, help_text="默认为可修改")

    class Meta:
        verbose_name = '服务参数'

        # unique_together = ('server', 'params_type', 'name', 'values')

        # unique_together = ('server_id', 'params_type', 'params_name', 'values_en')

    def __str__(self):
        # queryset = self.objects.filter(parent_id=None)
        # return queryset.values("params_name_display", "params_name")
        return "%s-%s-%s" % (self.params_name_display, self.params_name, self.values_display)


@python_2_unicode_compatible
class ServerParams(models.Model):
    CH_SETTING_TYPE = (
        ('SELECT', '选择参数'),
        ('INPUT', '输入参数')
    )
    CH_INTERFACE_TYPE = (
        ('INT','整形'),
        ('STR', '字符串'),
        ('LIST', '列表/数组'),
        ('DICT', '字典')
    )
    PARAMS_PURPOSE_TYPE = (
        ('PAGE_PARAM', '页面'),
        ('INTERFACE_PARAM', '接口')
    )
    server_id = models.SmallIntegerField(verbose_name=_("所属服务"))
    params_type = models.CharField(_("参数类型"), max_length=64)
    params_purpose = models.CharField(_("参数用途"), max_length=64, choices=PARAMS_PURPOSE_TYPE, default='PAGE_PARAM')
    params_name = models.CharField(_("参数简称"), max_length=100, help_text="英文，与页面名称保持一致", unique=True)
    params_name_display = models.CharField(_("参数名称"), max_length=255, help_text="中文，与页面名称保持一致",
                                           null=True, blank=True)
    param_option = JsonField(_("参数额外字段"), default={})
    param_comment = models.TextField(_("参数注释"), null=True, blank=True)
    is_editable = models.BooleanField(default=True)
    class Meta:
        verbose_name = '服务参数'
        verbose_name_plural = verbose_name

    def __str__(self):
        return "%s_%s" % (self.params_name_display, self.params_name)


@python_2_unicode_compatible
class ServerParamValues(models.Model):
    CH_SETTING_TYPE = (
        ('SELECT', '下拉参数'),
        ('INPUT', '输入参数')
    )
    param_id = models.SmallIntegerField(_("参数ID"))
    param_ins = models.ForeignKey(verbose_name=_("参数对象"), to=ServerParams, related_name="param_value", null=True,
                                  blank=True, on_delete=models.CASCADE)
    param_value_name = models.CharField(_("参数值名称"), max_length=255, null=True, blank=True)
    param_value_tag_name = models.CharField(_("参数值标识"), max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = '服务参数'
        verbose_name_plural = verbose_name

    def __str__(self):
        return "%s_%s" % (self.param_value_name, self.param_value_tag_name)


class PrimaryApplication(models.Model):
    number = models.SmallIntegerField(_('序号'), null=True, blank=True)
    local_app_number = models.CharField(_('本地应用编号'), max_length=64)
    app_short_name = models.CharField(_('应用简称'), max_length=64)
    app_name = models.CharField(_('应用名称'), max_length=100)
    recovery_sys_level = models.CharField(_('灾备等级'), max_length=32)
    application_level = models.CharField(_('应用等级'), max_length=32, null=True, blank=True)
    deploy_location = models.CharField(_('部署地点'), max_length=32, null=True, blank=True)
    ITOMer = models.CharField(_('运维负责人'), max_length=32, null=True, blank=True)
    develop_group = models.CharField(_('开发负责组'), max_length=64, null=True, blank=True)
    full_time_service = models.BooleanField(_("24小时客服服务"), default=False)
    system_app_source = models.CharField(_('系统应用来源'), max_length=64, null=True, blank=True)
    outsourcing_company = models.CharField(_('外购公司'), max_length=64, null=True, blank=True)
    operation_lead_department = models.CharField(_('业务牵头部门'), max_length=64, null=True, blank=True)
    cooperate_department = models.CharField(_('配合部门'), max_length=64, null=True, blank=True)
    institution_department = models.CharField(_('制度流程制定部门'), max_length=64, null=True, blank=True)
    user_permission_department = models.CharField(_('用户权限管理部门'), max_length=64, null=True, blank=True)
    app_introduction = models.TextField(_('应用简介'), null=True, blank=True)
    # app_node_ip = models.GenericIPAddressField(_("应用ip节点"), null=True, blank=True)

    def __str__(self):
        return "%s-%s" % (self.app_name, self.app_short_name)


class SecondaryApplication(models.Model):
    # number = models.SmallIntegerField(_('父级序号'))
    parent_app = models.ForeignKey(verbose_name=_('父级应用'), to=PrimaryApplication, related_name="secondary")
    local_app_number = models.CharField(_('本地应用编号'), max_length=64)
    app_short_name = models.CharField(_('二级应用简称'), max_length=64)
    app_name = models.CharField(_('二级应用名称'), max_length=100)
    recovery_sys_level = models.CharField(_('灾备等级'), max_length=32, null=True, blank=True)
    application_level = models.CharField(_('应用等级'), max_length=32, null=True, blank=True)
    deploy_location = models.CharField(_('部署地点'), max_length=32, null=True, blank=True)
    ITOMer = models.CharField(_('运维负责人'), max_length=32, null=True, blank=True)
    develop_group = models.CharField(_('开发负责组'), max_length=64, null=True, blank=True)
    full_time_service = models.BooleanField(_("24小时客服服务"), default=False)
    system_app_source = models.CharField(_('系统应用来源'), max_length=64, null=True, blank=True)
    outsourcing_company = models.CharField(_('外购公司'), max_length=64, null=True, blank=True)
    operation_lead_department = models.CharField(_('业务牵头部门'), max_length=64, null=True, blank=True)
    cooperate_department = models.CharField(_('配合部门'), max_length=64, null=True, blank=True)
    institution_department = models.CharField(_('制度流程制定部门'), max_length=64, null=True, blank=True)
    user_permission_department = models.CharField(_('用户权限管理部门'), max_length=64, null=True, blank=True)
    app_introduction = models.TextField(_('应用简介'), null=True, blank=True)
    # app_node_ip = models.GenericIPAddressField(_("应用ip节点"), null=True, blank=True)


@python_2_unicode_compatible
class ServerMatchingRule(models.Model):
    CH_MATCHING_TYPE = (
        ('AND', '和'),
        ('OR', '或')
    )
    # param = models.ForeignKey(verbose_name=_("参数对象"), to=ServerParams, related_name="server_matching_rule", null=True,
    #                           blank=True)
    # param_name = models.CharField(_("参数名称"), max_length=64, null=True, blank=True)
    param_id = models.SmallIntegerField(_("参数ID"))
    param_of_server_id = models.SmallIntegerField(_("参数来源服务"), null=True, blank=True)
    param_value_id = JsonField(_("参数值ID"), default=[])
    # param_value = JsonField(_("参数值"), default=[])
    comment = JsonField(_("备注"), default={})

    param_matching_pattern = models.CharField(_("参数匹配方式"), max_length=64, choices=CH_MATCHING_TYPE, default="AND",
                                              null=True, blank=True)

    class Meta:
        verbose_name = "服务参数匹配规则"
        verbose_name_plural = verbose_name
        # unique_together = ("param_name", "param_value")
    def __str__(self):
        ins = ServerParams.objects.filter(id=self.param_id).first()
        return "%s的匹配规则" % (ins.params_name_display)


@python_2_unicode_compatible
class MatchedCondition(models.Model):
    matching_rule = models.ForeignKey(verbose_name=_("匹配条件的匹配对象"), to=ServerMatchingRule,on_delete=models.CASCADE,
                                      related_name="matched_condition", null=True, blank=True)
    matching_param = models.ForeignKey(verbose_name=_("匹配参数对象"), to=ServerParams, on_delete=models.SET_NULL,
                                       related_name="matching_param_condition", null=True, blank=True)
    # matching_param_value = models.CharField(_("匹配条件参数值"), max_length=64, null=True, blank=True)
    matching_param_value_id = models.SmallIntegerField(_("匹配条件参数值ID"), null=True, blank=True)
    comment = JsonField(_("备注"), default={})

    class Meta:
        verbose_name = "服务参数匹配条件"
        verbose_name_plural = verbose_name

    def __str__(self):
        ins = ServerParams.objects.filter(id=self.matching_rule.param_id).first()
        return "%s匹配规则的条件" % (ins.params_name_display)
