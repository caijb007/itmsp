# coding: utf-8
# Author: ld
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from itmsp.utils.fields import JsonField
from itmsp.models import *

from django.utils.timezone import now
from iuser.models import ExUser


class NetworkSegment(models.Model):
    """
    虚拟环境网络
    """
    name = models.CharField(max_length=255, unique=True, null=True)
    net = models.GenericIPAddressField(protocol='ipv4', unique=True)
    netmask = models.CharField(default=24, max_length=100)
    inited = models.BooleanField(default=False)
    description = models.CharField(max_length=255, default=None, null=True)


class IPUsage(models.Model):
    """
    IP地址池
    """
    network = models.ForeignKey('NetworkSegment', null=True, on_delete=models.SET_NULL, related_name='ipusage')
    ipaddress = models.GenericIPAddressField(protocol='ipv4')
    is_occupy = models.BooleanField(default=False)  # 占用
    is_ping = models.BooleanField(default=False)  # 是否ping通
    is_avaliable = models.BooleanField(default=False)  #
    is_lock = models.BooleanField(default=False)  # 是否锁定


class VMGenerateApproval(models.Model):
    """
    vmware资源申请表
    """
    APPROVAL_STATUS = (
        (0, u"未提交/退回"),
        (1, u"已提交"),
        (2, u"已审批"),
        (3, u"处理中"),
        (4, u"已完成"),
        (-1, u"错误未处理"),
    )
    title = models.CharField(_("申请标题"), max_length=64, null=True, blank=True)
    approval_number = models.CharField(_("申请编号"), max_length=100, null=True, blank=True)
    status = models.SmallIntegerField(choices=APPROVAL_STATUS, default=0)
    # deploy_place = models.CharField(_("部署地点"), max_length=64)
    env_type = models.CharField(_("环境类型"), max_length=64, null=True, blank=True)
    # os_type = models.CharField(_("操作系统"), max_length=64)
    applicant = models.ForeignKey(verbose_name=_("申请人"), to=ExUser, null=True, blank=True)
    apply_msg = models.TextField(_("申请信息"), null=True, blank=True)
    apply_date = models.DateTimeField(_(u"申请时间"), default=now, help_text="默认时间为创建时间")
    workflow_number = models.CharField(_("所属流程编号"), max_length=255, null=True, blank=True)
    blue_ins_number = models.CharField(_("所属蓝图实例编号"), max_length=255, null=True, blank=True)
    map_relation = JsonField(_("映射关系"), default={})

    @property
    def status_display(self):
        return self.get_status_display()

    def __str__(self):
        return self.approval_number


@python_2_unicode_compatible
class VMGenerateApprovalOrd(models.Model):
    """
    vmware申请数据
    """
    approval = models.ForeignKey("VMGenerateApproval", related_name='vm_generate_ord')
    env_type = models.CharField(_("环境类型"), max_length=64)

    apply_deploy_place = models.CharField(_("部署地点"), max_length=64, null=True, blank=True)
    apply_os_version = models.CharField(_("系统版本"), max_length=64, null=True, blank=True)
    apply_node_type = models.CharField(_("节点类型"), max_length=64, null=True, blank=True)
    apply_network_area = models.CharField(_("网络区域"), max_length=64, null=True, blank=True)
    apply_application = JsonField(default=[])
    apply_software = JsonField(default=[])
    apply_cpu = models.SmallIntegerField()
    apply_memory_gb = models.IntegerField()
    apply_disk_gb = models.IntegerField()

    apply_expiration = models.CharField(max_length=64, null=True, blank=True)
    apply_system = JsonField(_("操作系统"), default={})
    apply_filesystem = JsonField(_("文件系统"), default={})

    class Meta:
        verbose_name = "申请工单表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "%s的详细表单" % (self.approval.approval_number)


class VMGenerateApprove(models.Model):
    APPROVE_STATUS = (
        (0, u"未提交/退回"),
        (1, u"已提交"),
        (2, u"已审批"),
        (3, u"处理中"),
        (4, u"已完成"),
        (-1, u"错误未处理"),
    )
    title = models.CharField(_("审批标题"), max_length=64, null=True, blank=True)
    blue_ins_number = models.CharField(_("所属蓝图实例编号"), max_length=255, null=True, blank=True)
    approval_number = models.CharField(_("申请编号"), max_length=100, null=True, blank=True)
    approve_number = models.CharField(_("审批编号"), max_length=100, null=True, blank=True)
    workflow_number = models.CharField(max_length=100, null=True, blank=True)
    workflow_note_ins_id = models.SmallIntegerField(null=True, blank=True)
    status = models.SmallIntegerField(choices=APPROVE_STATUS, default=0)
    # deploy_place = models.CharField(_("部署地点"), max_length=64)
    # env_type = models.CharField(_("环境类型"), max_length=64)
    # os_type = models.CharField(_("操作系统"), max_length=64)
    aprover = models.CharField(verbose_name=_("审批人"), max_length=64, null=True, blank=True)
    approve_msg = models.TextField(_("审批信息"), null=True, blank=True)
    approve_date = models.DateTimeField(_(u"审批时间"), default=now, help_text="默认时间为创建时间")
    approve_result = JsonField(_("审批结果"), default={})
    map_relation = JsonField(_("映射关系"), default={})


class VMGenerateApproveOrd(models.Model):
    """
    vm生成审批表数据
    """
    approve = models.ForeignKey("VMGenerateApprove", related_name='vm_generate_approve_ord')
    env_type = models.CharField(_("环境类型"), max_length=64)

    deploy_location = models.CharField(_("部署地点"), max_length=64, null=True, blank=True)
    appro_os_version = models.CharField(_("系统版本"), max_length=64, null=True, blank=True)
    node_type = models.CharField(_("节点类型"), max_length=64, null=True, blank=True)
    network_area = models.CharField(_("网络区域"), max_length=64, null=True, blank=True)
    application = JsonField(default=[])
    software = JsonField(default=[])
    target_cpu_cores = models.SmallIntegerField()
    target_mem_gb = models.IntegerField()
    add_datadisk_gb = models.IntegerField()
    expiration = models.CharField(max_length=64, null=True, blank=True)
    system_type = JsonField(_("操作系统"), default={})
    apply_filesystem = JsonField(_("文件系统"), default={})
    # 用户自定义软件挂载点和所需磁盘空间大小
    custom_path = JsonField(default={})
    custom_disk = JsonField(default={})
    custom_add_path = JsonField(default={})
    appro_resource = JsonField(default=[])
    configuration_resource_information = JsonField(_('配置资源信息'), default={})
