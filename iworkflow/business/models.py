# coding: utf-8
# Author: Chery-Huo
# 这里我们假设一个业务表 或者叫做  工单表

from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from iworkflow.models import  ProcessCategory,ProcessDefinition,TaskNode,TaskDefinition
import datetime

FORMAT_DATETIME = datetime.datetime.strptime('2019-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
FORMAT_DATE = default = datetime.datetime.strptime('2019-01-01', "%Y-%m-%d")

'业务和流程关系映射表'

@python_2_unicode_compatible
class WorkflowAndBusiness(models.Model):
    """
    业务和流程关系映射表
    """
    workflowKey = models.CharField(_("流程启动key"),max_length=64)
    pCategory = models.ForeignKey(to=ProcessCategory, null=True, blank=True, verbose_name="流程分类")
    pDefinition = models.ForeignKey(to=ProcessDefinition, null=True, blank=True, verbose_name="流程定义")
    pNode = models.ManyToManyField(to=TaskNode,  verbose_name="流程节点")
    taskDefinition = models.ManyToManyField(to=TaskDefinition, blank=True, verbose_name="任务定义")
    module1 = models.CharField(max_length=64, null=True, blank=True, verbose_name="模块1")
    module2 = models.CharField(max_length=64,  null=True, blank=True, verbose_name="模块2")
    createTime = models.DateTimeField(_(u"创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = "业务和流程"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.workflowKey

from itmsp.utils.fields import JsonField
# 实例操作记录表
@python_2_unicode_compatible
class WorkflowLog(models.Model):
    pInstance_number = models.CharField(_("流程实例编号"), max_length=64)
    suggestion = models.CharField(_("处理意见"), max_length=1000, null=True, blank=True)
    participant = models.CharField(_('处理人'), max_length=50, blank=True, null=True)
    taskInstanceId = models.CharField(_('当前任务实例id'), max_length=32, blank=True, null=True)
    intervene_type_id = models.IntegerField(_('记录类型'), default=0, help_text='0.申请记录，1.审批记录', null=True, blank=True)
    business_data = JsonField(default=[])
    business_map_relation = JsonField(default=[])
    business_blue_info = JsonField(default={},null=True, blank=True)

    creator = models.CharField(_(u'创建人'), max_length=50, help_text="关联的是user", null=True, blank=True)
    createTime = models.DateTimeField(_(u"创建时间"), auto_now_add=True)
    updateTime = models.DateTimeField(_(u"更新时间"), null=True, blank=True, auto_now=True)
    is_deleted = models.BooleanField(_(u'已删除'), default=False)

    class Meta:
        verbose_name = '实例流转操作日志'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.pInstance_number