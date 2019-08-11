# -*- coding: utf-8 -*-
# Author: Chery-Huo
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.db import models
from itmsp.utils.fields import JsonField
# from django.contrib.postgres.fields import  JSONField
from django.utils.timezone import now
from django.utils.encoding import python_2_unicode_compatible

__all__ = [
    'ProcessCategory',
    'ProcessDefinition',
    'TaskNode',
    'TaskDefinition',
    'ProcessInstance',
    'TaskInstance',
    'BusinessToProcess',
    'BusinessAndId',
    'ProcessInstanceRecord'
]
PENDING = 0
APPROVED = 1
REJECTED = 2

"default=datetime.datetime.strptime('0001-01-01 00:00:00', '%Y-%m-%d %H:%m:%s')"


# 流程类型表
@python_2_unicode_compatible
class ProcessCategory(models.Model):
    id = models.AutoField(_("流程类型ID"), primary_key=True)
    processCategoryName = models.CharField(_(u"流程类型名称"), max_length=64)
    processCategoryKey = models.CharField(_(u"流程类型key"), max_length=64)
    createTime = models.DateTimeField(_(u"创建时间"), auto_now_add=True)
    updateTime = models.DateTimeField(_(u"更新时间"), null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "流程类型"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.processCategoryName
    # def save(self, force_insert=False, force_update=False, using=None,
    #          update_fields=None):
    # super(ProcessCategory, self).__init__()
    # strtimes = datetime.datetime.strftime(self.createTime,'%Y-%m-%d %H:%m:%s' )
    # return "%s",strtimes


# # 流程配置表 暂时并没有用到~
# class ProcessConfig(models.Model):
#     id = models.AutoField("流程配置ID", primary_key=True)
#     processConfigKey = models.CharField("流程配置key:开发人员自定义的唯一的业务编码", max_length=64)
#     processCategoryId = models.ForeignKey(to=ProcessCategory, verbose_name="流程类型ID")
#     processDefinitionId = models.ForeignKey("ProcessDefinition", verbose_name="流程定义ID")
#     createTime = models.DateTimeField(_(u"创建时间"), auto_now_add=True)
#     updateTime = models.DateTimeField(_(u"更新时间"), null=True, blank=True, auto_now=True)
#
#     class Meta:
#         verbose_name = "流程配置"
#         verbose_name_plural = verbose_name
#
#     def __str__(self):
#         return str(self.id)


# 流程定义表
@python_2_unicode_compatible
class ProcessDefinition(models.Model):
    id = models.AutoField("流程定义ID", primary_key=True)
    pCategoryKey = models.ForeignKey(verbose_name=u"所属流程类型", to=ProcessCategory)
    processDefinitionName = models.CharField(u"流程定义名称", max_length=64)
    processDefinitionKey = models.CharField(u"流程定义key", max_length=64)
    processNodes = models.PositiveIntegerField(u"流程总节点", default=0, help_text="默认设置为0 即无流程节点")
    is_deleted = models.BooleanField(u"是否删除", default=False, help_text="默认不删除")
    createTime = models.DateTimeField(_(u"创建时间"), auto_now_add=True)
    updateTime = models.DateTimeField(_(u"更新时间"), null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "流程定义"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.processDefinitionName


# 流程节点名称表
@python_2_unicode_compatible
class TaskNode(models.Model):
    # taskNameId = models.IntegerField(u"流程定义ID")
    id = models.AutoField(_('流程节点ID'), primary_key=True)
    pCategoryKey = models.ForeignKey(to=ProcessCategory, verbose_name="流程类型key")
    taskName = models.CharField(u"流程节点名称", max_length=64)
    taskKey = models.CharField(u"流程节点key", max_length=64)
    createTime = models.DateTimeField(_(u"创建时间"), auto_now_add=True)
    updateTime = models.DateTimeField(_(u"更新时间"), null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "流程节点"
        verbose_name_plural = verbose_name

    def __str__(self):
        # print '123'
        return u"%s" % self.taskName


from iuser.models import ExUser


# 任务定义表

@python_2_unicode_compatible
class TaskDefinition(models.Model):
    # taskDefinitionId = models.IntegerField(u"任务定义id")
    id = models.AutoField("任务定义id", primary_key=True)
    pDefinitionId = models.ForeignKey(to=ProcessDefinition, verbose_name="所属流程定义id", related_name='task_def')
    taskName = models.ForeignKey(to=TaskNode, verbose_name="任务名称")
    # candidate = models.CharField(u"候选人id", max_length=64)
    candidate = models.ManyToManyField(verbose_name="候选人id", to=ExUser, )
    taskNode = models.PositiveIntegerField(u"任务所处的节点", default=1)
    createTime = models.DateTimeField(_(u"创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = "任务定义"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.taskName.taskName


# 流程实例表
@python_2_unicode_compatible
class ProcessInstance(models.Model):
    SAVED = 3
    PENDING = 0
    APPROVED = 1
    REJECTED = 2
    PROCESS_STATUS = [
        (PENDING, _('进行中')),
        (APPROVED, _('执行成功')),
        (REJECTED, _('执行失败')),
        (SAVED, _('保存')),
    ]
    # processInstanceId = models.IntegerField(u"流程实例Id")
    id = models.AutoField("流程实例ID", primary_key=True, default=None)
    instance_name = models.CharField(_("实例名称"), max_length=100)
    pDefinitionId = models.ForeignKey(to=ProcessDefinition, verbose_name="流程定义id")
    businessKey = models.CharField(verbose_name="业务主键", null=True, blank=True, max_length=64)
    startTime = models.DateTimeField(_(u"流程启动时间"), default=now, help_text="默认时间为创建时间")
    endTime = models.DateTimeField(u"流程结束时间", null=True, blank=True)
    duration = models.IntegerField(u"流程执行时长", null=True, blank=True)
    startUserID = models.CharField(u"流程发起人Id", max_length=64, null=True, blank=True)
    currentProcessNode = models.ForeignKey(to=TaskDefinition, verbose_name="当前流程节点名字", related_name="task", null=True,
                                           blank=True)
    processStatus = models.IntegerField(u"流程状态", choices=PROCESS_STATUS, default=PENDING,
                                        help_text="默认为0执行中1执行成功 2 执行失败")

    # is_deleted = models.BooleanField(u"流程是否删除", default=False, help_text="默认不删除")

    class Meta:
        verbose_name = "流程实例"
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.id)

    def get_processStatus_display(field):
        return


# 任务实例表
@python_2_unicode_compatible
class TaskInstance(models.Model):
    # taskInstanceId = models.IntegerField(_(u"任务实例ID"))
    id = models.AutoField(_("任务实例ID"), primary_key=True)
    pInstanceId = models.ForeignKey(to=ProcessInstance, verbose_name="对应的流程实例", related_name="task_instance")
    pDefinitionId = models.ForeignKey(to=ProcessDefinition, verbose_name="流程定义的名称")
    # businessKey = models.CharField(u"业务数据主键", max_length=64)
    # businessKey = models.ForeignKey(to=BusinessInfo, null=True, blank=True)
    businessKey = models.CharField(verbose_name="业务主键", null=True, blank=True, max_length=64)
    tDefinitionId = models.ForeignKey(to=TaskDefinition, verbose_name="任务定义")
    taskName = models.CharField(u"任务名称", max_length=64)
    taskNode = models.ForeignKey(to=TaskNode, verbose_name="对应流程节点名称", null=True, blank=True)
    assignee = JsonField(default=[])
    startTime = models.CharField(u"开始时间", max_length=80, default=now, help_text="默认为当前时间", null=True, blank=True)
    endTime = models.CharField(u"结束时间", null=True, blank=True, max_length=80)
    duration = models.IntegerField(u"任务执行时长", null=True, blank=True, help_text="任务执行时长，单位毫秒")
    taskStatus = models.PositiveIntegerField(u"任务执行状态", default=0, help_text="任务状态0:任务未开启;1:任务开启中，2 任务执行成功,3:任务执行失败")
    comment = models.CharField(u"备注", max_length=500, null=True, blank=True)

    # is_deleted = models.BooleanField(u"任务是否删除", default=False, help_text="默认不删除")

    class Meta:
        verbose_name = "任务实例"
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.id)


'APPROVED'

# from itmsp.settings import FUNC_APPS as apps

APP1 = 0
APP2 = 1
APP3 = 2
APP4 = 3
apps = [
    (APP1, 'itmsp'),
    (APP2, 'iuser'),
    (APP3, 'ivmware'),
    (APP4, 'iworkflow')
]


@python_2_unicode_compatible
class BusinessToProcess(models.Model):
    id = models.AutoField(_("编号"), primary_key=True)
    business = models.IntegerField("业务模块", choices=apps, default=APP3, null=True, blank=True)
    tables = models.CharField("对应模块的表名", default="approve", max_length=64, null=True, blank=True,
                              help_text="尽量统一一个名字，默认表名为approve")

    class Meta:
        verbose_name = '业务模块'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.id)


@python_2_unicode_compatible
class BusinessAndId(models.Model):
    id = models.AutoField(_("编号"), primary_key=True)
    business_id = models.ForeignKey(to=BusinessToProcess, null=True, blank=True, verbose_name="所属业务名称")
    # table_name = models.CharField(_('所属表名称'), null=True, blank=True, max_length=64)
    table_id = models.CharField(_('所属表记录'), null=True, blank=True, max_length=64)

    class Meta:
        verbose_name = '业务模块编号对应表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.id)


@python_2_unicode_compatible
class ProcessInstanceRecord(models.Model):
    """
    流程实例记录表
    """
    blue_instance_number = models.CharField(_("流程实例"), max_length=64)
    blue_note = models.CharField(_("流程节点"), max_length=64)
    create_user = models.CharField(_("流程启动人"), max_length=64)
    examiner = models.CharField(max_length=64)
    node_status = models.CharField(_("节点状态"), max_length=64)
    blue_process_status = models.CharField(_("流程实例状态"), max_length=64)
    startTime = models.DateTimeField(_(u"流程启动时间"), default=now, help_text="默认时间为创建时间")
    endTime = models.DateTimeField(u"流程结束时间", null=True, blank=True)

    class Meta:
        verbose_name = '流程实例记录表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.blue_instance_number)
