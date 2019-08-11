# coding: utf-8
# Author: ld

from collections import Iterable
from itmsp.settings import IVM
from rest_framework import serializers
from .models import *


class NetworkSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSegment
        fields = "__all__"


class IPUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPUsage
        fields = "__all__"


class VMGenerateApprovalSerializer(serializers.ModelSerializer):
    apply_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    applicant = serializers.SlugRelatedField('name', read_only=True)

    # approver = serializers.SlugRelatedField('name', read_only=True)
    class Meta:
        model = VMGenerateApproval
        fields = '__all__'


class VMGenerateApprovalOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = VMGenerateApprovalOrd
        fields = '__all__'


class VMGenerateApproveSerializer(serializers.ModelSerializer):
    # apply_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    # applicant = serializers.SlugRelatedField('name', read_only=True)

    # approver = serializers.SlugRelatedField('name', read_only=True)

    class Meta:
        model = VMGenerateApprove
        fields = '__all__'


class VMGenerateApproveOrdSerializer(serializers.ModelSerializer):
    # appro_filesystem = serializers.DictField(source="VMGenerateApproveOrd.appro_filesystem",read_only=True)
    apply_filesystem = serializers.JSONField(default={})
    # approval_number = serializers.SerializerMethodField()
    approve = VMGenerateApproveSerializer()
    # def get_filesystem(self,obj):
    #     serializers
    #     appro_filesystem
    configuration_resource_information = serializers.JSONField(default={})
    application = serializers.JSONField(default={})

    class Meta:
        model = VMGenerateApproveOrd
        fields = '__all__'


###################################################################
##############################序列化################################
###################################################################
class BaseSerializer(object):
    """
    序列化器基类
    """

    def __init__(self, data=None, **kwargs):
        """
        * 参数
        ** detail - 详细信息 [bool]
        """
        self._data = data
        self._detail = kwargs.get('detail', False)
        self._current_data = self._data

    def data_info(self, *args):
        """
        简要信息
        * 返回字段
        ** name
        """
        data = self._current_data
        kwargs = dict()
        kwargs['name'] = data.name
        return kwargs

    @property
    def data(self):
        """
        返回数据
        """
        info = list()
        assert isinstance(self._detail, bool)
        is_iterable = isinstance(self._data, Iterable)
        if not self._data:
            return info
        if is_iterable:
            for data in self._data:
                self._current_data = data
                kwargs = self.data_info()
                if kwargs:
                    info.append(kwargs)
        else:
            info = self.data_info()
        return info


class DatacenterSerializer(BaseSerializer):
    """
    数据中心数据处理
    """

    def data_info(self):
        """
        * 返回字段
        ** moid
        ** name
        """
        data = self._current_data
        kwargs = super(DatacenterSerializer, self).data_info()
        if kwargs and self._detail:
            pass
        return kwargs


class ClusterSerializer(BaseSerializer):
    """
    集群数据处理
    """

    def data_info(self):
        """
        * 返回字段
        ** moid
        ** name
        """
        data = self._current_data
        kwargs = super(ClusterSerializer, self).data_info()
        if kwargs and self._detail:
            pass
        return kwargs

    @property
    def best_host_of_mb(self):
        """
        内存最优主机
        """
        data = self._current_data
        hosts = data.host
        best_host = None
        best_perform = 0
        for host in hosts:
            host_serializer = HostSystemSerializer(host).data
            free_mem_mb = host_serializer.get('free_mem_mb')
            if free_mem_mb > best_perform:
                best_perform = free_mem_mb
                best_host = host
        return best_host


class HostSystemSerializer(BaseSerializer):
    """
    主机数据处理
    """

    def data_info(self):
        """
        * 返回字段
        ** moid
        ** name
        ** vmotion_enable
        ** total_cpu_cores
        ** total_cpu_mhz
        ** total_mem_mb
        ** usage_cpu_mhz
        ** usage_mem_mb
        ** in_maintenance_mode
        """
        data = self._current_data
        kwargs = super(HostSystemSerializer, self).data_info()
        total_mem_mb = data.summary.hardware.memorySize / 1024 ** 2
        usage_mem_mb = data.summary.quickStats.overallMemoryUsage
        kwargs['usage_mem'] = usage_mem_mb * 100 / total_mem_mb
        if kwargs and self._detail:
            runtime = data.runtime
            summary = data.summary
            summary_hardware = summary.hardware
            summary_stat = summary.quickStats

            kwargs['vmotion_enable'] = summary.config.vmotionEnabled
            kwargs['total_cpu_cores'] = summary_hardware.numCpuCores
            kwargs['total_cpu_mhz'] = summary_hardware.cpuMhz
            kwargs['total_mem_mb'] = summary_hardware.memorySize / 1024 ** 2
            kwargs['usage_cpu_mhz'] = summary_stat.overallCpuUsage
            kwargs['usage_mem_mb'] = summary_stat.overallMemoryUsage
            kwargs['in_maintenance_mode'] = runtime.inMaintenanceMode
            kwargs['free_mem_mb'] = kwargs['total_mem_mb'] - kwargs['usage_mem_mb']

        return kwargs

    @staticmethod
    def get_best_host_of_mb(hosts):
        best_host = None
        best_perform = 0
        for host in hosts:
            host_data = HostSystemSerializer(host, detail=True).data
            free_mem_mb = host_data.get('free_mem_mb')
            if free_mem_mb > best_perform:
                best_perform = free_mem_mb
                best_host = host
        return best_host

    @staticmethod
    def get_best_datastore_for_host(datastores):
        best_datastore = None
        best_ds_perform = IVM['RESOURCE_LIMIT_DS']
        for datastore in datastores:
            datastore_serializer = DataStoreSerializer(datastore, detail=True)
            datastore_detail = datastore_serializer.data_info()
            if not (datastore_detail.pop('accessible') and datastore_detail.pop('maintenance_mode') == "normal"):
                continue
            datastore_name = datastore_detail.pop('name')
            # BAN掉指定的LUN
            bans = IVM['RESOURCE_BAN_DS']
            for ban in bans:
                if datastore_name.find(ban):
                    continue
            total_space_mb = datastore_detail.pop('total_space_mb')
            free_space_mb = datastore_detail.pop('free_space_mb')
            ds_perform = (total_space_mb - free_space_mb) * 100 / total_space_mb
            if ds_perform < best_ds_perform:
                best_ds_perform = ds_perform
                best_datastore = datastore
        return best_datastore

    @property
    def best_datastore(self):
        """
        主机存储最优
        """
        data = self._current_data
        datastores = data.datastore
        best_datastore = None
        best_ds_perform = IVM['RESOURCE_LIMIT_DS']
        for datastore in datastores:
            datastore_serializer = DataStoreSerializer(datastore, detail=True)
            datastore_detail = datastore_serializer.data_info()
            if not (datastore_detail.pop('accessible') and datastore_detail.pop(
                    'multi_hosts_access') and datastore_detail.pop('maintenance_mode') == "normal"):
                continue
            datastore_name = datastore_detail.get('name')
            # BAN掉指定的LUN
            bans = IVM['RESOURCE_BAN_DS']
            for ban in bans:
                if datastore_name.find(ban):
                    continue
            total_space_mb = datastore_detail.get('total_space_mb')
            free_space_mb = datastore_detail.get('free_space_mb')
            ds_perform = (total_space_mb - free_space_mb) * 100 / total_space_mb
            if ds_perform < best_ds_perform:
                best_ds_perform = ds_perform
                best_datastore = datastore

        return best_datastore


class ResourcePoolSerializer(BaseSerializer):
    """
    资源池数据处理
    """

    def data_info(self):
        """
        * 返回字段
        ** moid
        """
        data = self._current_data
        kwargs = super(ResourcePoolSerializer, self).data_info()
        if kwargs and self._detail:
            summary = data.summary
        return kwargs


class DataStoreSerializer(BaseSerializer):
    """
    数据存储 数据处理
    """

    def data_info(self):
        """
        * 返回字段
        ** accessible
        ** multi_hosts_access
        ** maintenance_mode
        ** url
        ** total_space_mb
        ** free_space_mb
        """
        data = self._current_data
        kwargs = super(DataStoreSerializer, self).data_info()
        total_space_mb = data.summary.capacity / 1024 ** 2
        free_space_mb = data.summary.freeSpace / 1024 ** 2
        usage_space_mb = total_space_mb - free_space_mb
        kwargs['usage_space'] = usage_space_mb * 100 / total_space_mb
        if kwargs and self._detail:
            summary = data.summary
            kwargs['accessible'] = summary.accessible
            kwargs['multi_hosts_access'] = summary.multipleHostAccess
            kwargs['maintenance_mode'] = summary.maintenanceMode

            if summary.accessible:
                kwargs['url'] = summary.url
                kwargs['total_space_mb'] = summary.capacity / 1024 ** 2
                kwargs['free_space_mb'] = summary.freeSpace / 1024 ** 2
                kwargs['usage_space_mb'] = kwargs['total_space_mb'] - kwargs['free_space_mb']
        return kwargs


class NetworkSerializer(BaseSerializer):
    """
    网络数据处理
    """

    def data_info(self):
        """
        * 返回字段
        """
        data = self._current_data
        kwargs = super(NetworkSerializer, self).data_info()
        kwargs['net'] = kwargs['name'].split('-')[-1]
        if kwargs and self._detail:
            summary = data.summary
            kwargs['ipPoolName'] = summary.ipPoolName
            kwargs['ipPoolId'] = summary.ipPoolId
        return kwargs


class VirtualMachineSerializer(BaseSerializer):
    """
    虚拟机数据处理
    """

    def __init__(self, data, **kwargs):
        super(VirtualMachineSerializer, self).__init__(data, **kwargs)

    def data_info(self):
        """
        * 返回字段
        ** power_state
        ** istemplate
        ** annotation
        ** cpu_num
        ** cpu_cores
        ** memory_mb
        ** storage_mb
        ** guestos_shortname
        ** guestos_fullname
        """
        data = self._current_data
        kwargs = super(VirtualMachineSerializer, self).data_info()
        if kwargs:
            config = data.config
            if self._detail:
                summary = data.summary
                # guest = data.guest
                config_hardware = config.hardware
                summary_config = summary.config
                summary_guest = summary.guest
                kwargs['power_state'] = summary.runtime.powerState
                kwargs['istemplate'] = config.template
                kwargs['annotation'] = config.annotation
                kwargs['cpu_num'] = config_hardware.numCPU
                kwargs['cpu_cores'] = config_hardware.numCoresPerSocket
                kwargs['memory_mb'] = config_hardware.memoryMB
                kwargs['storage_mb'] = summary.storage.committed / 1024 ** 2
                kwargs['guestos_shortname'] = summary_config.guestId
                kwargs['guestos_fullname'] = summary_config.guestFullName
                kwargs['ipadderss'] = summary_guest.ipAddress
                kwargs['host_name'] = summary_guest.hostName
        return kwargs


class CustomSpecSerializer(BaseSerializer):
    """
    自定义规则
    """

    def data_info(self):
        """
        * 返回字段
        """
        data = self._current_data
        kwargs = {}
        kwargs['name'] = data.name
        if self._detail:
            kwargs['description'] = data.description
            kwargs['type'] = data.type
            kwargs['changeVersion'] = data.changeVersion
            kwargs['lastUpdateTime'] = data.lastUpdateTime
        return kwargs
