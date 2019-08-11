# coding: utf-8
# Author: ld
import sys
import ssl
import time
import warnings
from pyVim.connect import SmartConnect
from pyVmomi import vim
from pyVmomi import vmodl
from itmsp.settings import IVM
from threading import Thread
from Queue import Queue
import json
from ..utils import *

_sis = {}
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
ssl_context.verify_mode = ssl.CERT_NONE
warnings.filterwarnings("ignore")
reload(sys)
sys.setdefaultencoding('utf-8')

# 默认子网掩码24位
DEFAULT_SUBNETMASK = "255.255.255.0"
SUCCESS = 'success'
FAULT = 'fault'
MAX_DEPTH = 10


def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.next()
        return cr

    return start


def wait_for_tasks(service_instance, tasks):
    """Given the service instance si and tasks, it returns after all the
    tasks are complete
    """
    property_collector = service_instance.content.propertyCollector
    task_list = [str(task) for task in tasks]
    # Create filter
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                 for task in tasks]
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                               pathSet=[],
                                                               all=True)
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = [property_spec]
    pcfilter = property_collector.CreateFilter(filter_spec, True)
    try:
        version, state = None, None
        # Loop looking for updates till the state moves to a completed state.
        while len(task_list):
            update = property_collector.WaitForUpdates(version)
            for filter_set in update.filterSet:
                for obj_set in filter_set.objectSet:
                    task = obj_set.obj
                    for change in obj_set.changeSet:
                        print task.info
                        if change.name == 'info':
                            state = change.val.state
                        elif change.name == 'info.state':
                            state = change.val
                        else:
                            continue
                        if not str(task) in task_list:
                            continue
                        if state == vim.TaskInfo.State.success:
                            # Remove task from taskList
                            task_list.remove(str(task))
                        elif state == vim.TaskInfo.State.error:
                            print task.info.error
                            raise Exception(task.info.error)
            # Move to next version
            version = update.version
    except vim.fault as e:
        raise Exception(e.msg)
    finally:
        if pcfilter:
            pcfilter.Destroy()


def get_moid(vimobj):
    """
    获取vim对象moid
    :param vimobj:  vim对象
    :return:  moid
    """
    return str(vimobj._GetMoId())


def default_gateway(ipadderss):
    """
    默认24位掩码时网关
    """
    ip = ipadderss.split('.')
    ip[-1] = str(254)
    geteway = '.'.join(ip)
    return geteway


def change_customspec(content, spec_name, ipaddress, gateway=None, subnetMask=None, dns=None):
    """
    配置自定义规范
    """
    custom_manage = content.customizationSpecManager
    spec_item = custom_manage.Get(spec_name)
    spec = spec_item.spec
    adapter = spec.nicSettingMap[0].adapter
    # 设置ip
    fixip = vim.vm.customization.FixedIp()
    fixip.ipAddress = ipaddress
    adapter.ip = fixip
    # 设置网关
    if gateway:
        gateway = gateway
    else:
        gateway = [default_gateway(ipaddress)]
    adapter.gateway = gateway
    # 设置掩码
    if subnetMask:
        subnetMask = subnetMask
    else:
        subnetMask = DEFAULT_SUBNETMASK
    adapter.subnetMask = subnetMask

    adapter.dnsServerList = dns
    # 重写自定义规则
    custom_manage.OverwriteCustomizationSpec(spec_item)

    return spec


def create_customspec(content, old_spec_name):
    """
    复制自定义规则
    """
    try:
        custom_manage = content.customizationSpecManager
        spec_item = custom_manage.Get(old_spec_name)
        if not spec_item:
            raise Exception(u"自定义规则不存在, 请联系管理员")
        newspec_name = str(time.time())
        custom_manage.DuplicateCustomizationSpec(name=old_spec_name, newName=newspec_name)
    except Exception as e:
        raise e
    return newspec_name


class VimBase(object):
    """
    pyvmoi 接口
    """

    def __init__(self, ip, port, user, pwd, uuid=''):
        self.uuid = uuid
        self.ip = ip
        self.port = int(port)
        self.user = user
        self.pwd = pwd
        self._si = None
        self._content = None
        self._cur_session = None
        self.version = ''
        self._containerView = None
        # self.threaded()
        self.connect()

    def threaded(self):
        q = Queue()
        q.put(self._si)

        def run_target():
            time_pass = 5
            while time_pass:
                item = q.get()
                if item:
                    q.put(SUCCESS)
                    return
                else:
                    q.put(self._si)
                    time.sleep(1)
                    time_pass -= 1
            q.put(FAULT)

        def is_connect():
            while True:
                is_connect = q.get()
                if is_connect is not FAULT or is_connect is not SUCCESS:
                    q.put(is_connect)
                if is_connect == FAULT:
                    return FAULT
                if is_connect == SUCCESS:
                    return SUCCESS
                # time.sleep(1)

        Thread(target=run_target).start()
        Thread(target=is_connect).start()

    def connect(self):
        self._si = self.get_si()
        try:
            self._content = self._si.RetrieveContent()
            self._cur_session = self._content.sessionManager.currentSession
            if not self._cur_session and isinstance(self._cur_session, vim.UserSession):
                self._content.sessionManager.Login(self.user, self.pwd)
        except:
            self._si = SmartConnect(host=self.ip, user=self.user, pwd=self.pwd, port=self.port, sslContext=ssl_context)
            self._content = self._si.RetrieveContent()
            self._cur_session = self._content.sessionManager.currentSession
            self.uuid = self.get_uuid()
            self.set_si()
        finally:
            if not self._si:
                raise Exception(u"vCenter连接失败， 请联系管理员")
            self._content = self._si.RetrieveContent()
        self._content = self._si.RetrieveContent()

    def get_si(self):
        global _sis
        if _sis.has_key(self.uuid):
            return _sis[self.uuid]
        else:
            return None

    def set_si(self):
        global _sis
        _sis[self.uuid] = self._si

    def discover(self):
        self.uuid = ''
        self._si = SmartConnect(host=self.ip, user=self.user, pwd=self.pwd, port=self.port, sslContext=ssl_context)
        self._content = self._si.RetrieveContent()
        uuid = self.get_uuid()
        version = self.get_version()
        self.set_si()
        return uuid, version

    def get_uuid(self):
        return self._content.about.instanceUuid

    def get_version(self):
        return self._content.about.apiVersion

    def get_moid(self, vimobj):
        moid = get_moid(vimobj)
        return moid

    def get_vimobj(self, vimobjs=None, moid=None, viewType=None):
        """
        由moid 获取vim对象
        :param vimobjs:
        :param moid:
        :return:
        """
        vimobj = None
        if not vimobjs:
            vimobjs = self.get_type_Instances(viewType)
        for o in vimobjs:
            if self.get_moid(o) == moid:
                vimobj = o
        return vimobj

    def get_obj(self, vimtype=None, name=None, container=None):
        """
        Return an object by name, if name is None the
        first found object is returned
        """
        obj = None
        container_views = self.get_type_Instances(vimtype, container=container)
        for cv in container_views:
            if name:
                if cv.name == name:
                    obj = cv
                    break
        return obj

    def get_content(self):
        return self._content

    def _get_views(self, viewType, recursive=True, container=None):
        """
        获取Folder视图
        :param viewType:   视图类型 eg - [vim.VirtualMachine]
        :param resursive:  是否递归Folder
        :return:  实体view列表
        """
        content = self._content
        if container:
            container = container
        else:
            container = content.rootFolder  # starting point to look into
        viewType = viewType
        recursive = recursive
        self._containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)
        children = self._containerView.view
        return children

    def get_type_Instances(self, viewType, container=None):
        """
        获取指定类型实例列表
        :param viewType:  实例类型
        * 实例类型包括
        ** vim.Datacenter
        ** vim.VirtualMachine
        ** vim.VirtualApp
        ** vim.ComputeResource
        ** vim.ResourcePool
        ** vim.HostSystem
        ** vim.Network
        ** vim.Datastore
        ** vim.DistributedVirtualSwitch
        ** vim.DistributedVirtualPortgroup
        :return: 实例列表
        """
        children = self._get_views(viewType, container=container)
        instances = children
        self._containerView.DestroyView()
        return instances

    def all_datacenter(self):
        """
        获取所有datacenter
        :return:  datacenter列表
        """
        viewType = [vim.Datacenter]
        datacenters = self.get_type_Instances(viewType)
        return datacenters

    def get_virtualmachines(self):
        """
        获取所有虚拟机
        :return: 虚拟机列表
        """
        viewType = [vim.VirtualMachine]
        virtualmachines = self.get_type_Instances(viewType)
        return virtualmachines

    def get_template(self):
        """
        获取template目录下的虚拟机
        :param datacenter: 数据中心
        :return: 模板列表
        """
        all_datacenter = self.all_datacenter()
        template_list = list()
        for datacenter in all_datacenter:
            vm_folders = datacenter.vmFolder.childEntity
            for folder in vm_folders:
                if folder.name == "template":
                    for f in folder.childEntity:
                        if not hasattr(f, 'childEntity') and f.config.template:
                            template_list.append(f)
        return template_list

    def cluster_of_datacenter(self, datacenter):
        """
        获取datacenter关联的所有集群
        :return: 集群列表
        """
        viewType = [vim.ClusterComputeResource]
        clusters = self.get_type_Instances(viewType, container=datacenter)
        return clusters

    def host_of_datacenter(self, datacenter):
        """
        获取datacenter关联的所有主机
        :return:  主机列表
        """
        viewType = [vim.HostSystem]
        hosts = self.get_type_Instances(viewType, container=datacenter)
        return hosts

    def all_customspec(self):
        """
        获取自定义规则
        :return: 自定义规则列表
        """
        content = self._content
        custom_manager = content.customizationSpecManager
        info = custom_manager.info
        return info

    def datastore_of_datacenter(self, datacenter):
        """
        获取datacenter关联的存储
        """
        datastore = datacenter.datastore
        return datastore

    def datastore_of_host(self, host):
        """
        主机关联的存储
        """
        datastore = host.datastore
        return datastore

    def host_of_cluster(self, cluster):
        """
        获取集群中的主机
        :param cluster: 集群
        :return: 主机列表
        """
        hosts = cluster.host
        return hosts

    def resp_of_cluster(self, cluster):
        """
        获取集群关联的资源池
        :param cluster: 集群
        :return: 资源池列表
        """
        resp = cluster.resourcePool
        return resp

    def network_of_all(self):
        """
        获取所有网络
        :return: 网络列表
        """
        viewType = [vim.Network]
        networks = self.get_type_Instances(viewType)
        return networks

    def network_of_datacenter(self, datacenter):
        """
        获取datacenter中所有网络
        """
        network = datacenter.network
        return network

    def network_of_host(self, host):
        """
        获取主机网络
        """
        networks = host.network
        return networks

    def findvm_by_dnsname(self, vm_name):
        """
        以hostname查找目标vm
        """
        searchIndex = self._content.searchIndex
        vm = searchIndex.FindByDnsName(dnsName=vm_name, vmSearch=True)
        return vm

    def findvm_by_ip(self, ip, datacenter=None):
        """
        以ip查询虚拟机
        """
        searchIndex = self._content.searchIndex
        vm = searchIndex.FindByIp(ip=ip, vmSearch=True, datacenter=datacenter)
        return vm


class VimTasks(VimBase):
    """
    vc操作类
    """

    # 集合克隆，配置及开机接口
    def prod_vm(self,
                vm_name=None,
                vm_ip=None,
                dns=None,
                template_name=None,
                datastore_name=None,
                cluster_name=None,
                datacenter_name=None,
                hostsystem_name=None,
                gateway=None,
                subnetMask=None,
                network=None,
                target_cpu_cores=-1,
                target_mem_gb=-1,
                add_datadisk_gb=-1,
                node_type=None,
                apply_user=None,
                env_type=None,
                expiration=None,
                application=None,
                ):
        # 克隆
        self.clone_vm(
            vm_name,
            vm_ip,
            dns,
            template_name,
            datastore_name,
            cluster_name,
            datacenter_name,
            hostsystem_name,
            gateway,
            subnetMask
        )
        # 配置

        self.reconfig_vm(
            node_type=node_type,
            apply_user=apply_user,
            env_type=env_type,
            expiration=expiration,
            application=application,
            vm_name=vm_name,
            network=network,
            target_cpu_cores=target_cpu_cores,
            target_mem_gb=target_mem_gb,
            add_datadisk_gb=add_datadisk_gb,
        )
        # 开机
        self.poweron_vm(vm_name)

        return True

    def clone_vm(self,
                 vm_name=None,
                 vm_ip=None,
                 dns=None,
                 template_name=None,
                 datastore_name=None,
                 cluster_name=None,
                 datacenter_name=None,
                 hostsystem_name=None,
                 gateway=None,
                 subnetMask=None,
                 ):
        content = self._content
        si = self._si

        datacenter = self.get_obj([vim.Datacenter], datacenter_name)
        template = self.get_obj([vim.VirtualMachine], template_name, container=datacenter)
        destfolder = datacenter.vmFolder

        if datastore_name:
            datastore = self.get_obj([vim.Datastore], datastore_name)
        else:
            datastore = self.get_obj(
                [vim.Datastore], template.datastore[0].info.name)

        # if None, get the first one
        cluster = self.get_obj([vim.ClusterComputeResource], cluster_name, container=datacenter)
        hostsystem = self.get_obj([vim.HostSystem], hostsystem_name)
        if not cluster:
            cluster = hostsystem

        resource_pool = cluster.resourcePool
        virtual_machine = self.get_virtualmachines()
        template_fullname = None
        for vm in virtual_machine:
            if vm.name == template_name:
                template_fullname = vm.summary.config.guestFullName
                break

        # 根据虚拟机名判断系统类型(linux/windows)
        old_spec_name = None
        if "windows" in template_fullname.lower() or "windows" in template_name.lower():
            old_spec_name = IVM['WINDOWS_CUSTOM_SPEC_NAME']
        else:
            old_spec_name = IVM['LINUX_CUSTOM_SPEC_NAME']

        # 自定义规则
        newspec_name = create_customspec(content, old_spec_name)
        customspec = change_customspec(content, newspec_name, vm_ip, gateway=gateway, subnetMask=subnetMask, dns=dns)

        try:
            # set relospec
            # RelocateSpec 参数 * datastore-数据存储   * resource pool- 资源池， hostsystem - 主机
            relospec = vim.vm.RelocateSpec()
            relospec.datastore = datastore
            relospec.pool = resource_pool
            relospec.host = hostsystem
            # set clonespec
            clonespec = vim.vm.CloneSpec()
            clonespec.location = relospec
            clonespec.powerOn = False
            clonespec.template = False
            clonespec.customization = customspec
            # start clone task
            clone_task = template.CloneVM_Task(folder=destfolder, name=vm_name, spec=clonespec)
            wait_for_tasks(si, [clone_task])
            state = clone_task.info.state
            # result = clone_task.info.result

        except vim.fault.UncustomizableGuest:
            raise Exception(u'客户机自定义过程不支持指定的客户机操作系统')
        except vim.fault.VirtualHardwareVersionNotSupported:
            raise Exception(u"所选主机不支持此虚拟机版本")
        finally:
            # 删除自定义规则
            isdel = self.delete_customspec(newspec_name)
            if not isdel:
                raise Exception(u"删除自定义规则失败！")
        return state

    def reconfig_vm(self,
                    vm_name=None,
                    network=None,
                    target_cpu_cores=-1,
                    target_mem_gb=-1,
                    add_datadisk_gb=-1,
                    node_type=None,
                    apply_user=None,
                    env_type=None,
                    expiration=None,
                    application=None,
                    ):
        """
        重新配置虚拟机
        """
        si = self._si
        try:
            virtualmachine = self.get_obj([vim.VirtualMachine], vm_name)
            config_spec = vim.vm.ConfigSpec()
            # Update VM Devices
            deviceChange = list()
            annotation = virtualmachine.config.annotation

            annotation = annotation_format(annotation, node_type=node_type, apply_user=apply_user, env_type=env_type,
                                           application=application, expiration=expiration)

            config_spec.annotation = annotation
            if target_cpu_cores > 0:
                config_spec.numCoresPerSocket = 1
                # target_cpu_num = target_cpu_cores * 2
                config_spec.numCPUs = target_cpu_cores
            if target_mem_gb > 0:
                config_spec.memoryMB = target_mem_gb * 1024
            if add_datadisk_gb > 0:
                disk_spec = self.get_disk_spec(virtualmachine, add_datadisk_gb)
                deviceChange.append(disk_spec)

            if network:
                network = self.get_obj([vim.Network], network)
                network_spec = self.get_network_spec(virtualmachine, network)
                if network_spec:
                    deviceChange.append(network_spec)
                else:
                    raise Exception(u"Ethernet adapter is not fount")
            config_spec.deviceChange = deviceChange
            reconfig_task = virtualmachine.ReconfigVM_Task(spec=config_spec)
            wait_for_tasks(si, [reconfig_task])
            result = reconfig_task.info.state
        except vim.fault.InvalidPowerState:
            raise Exception(r'虚拟机电源状态异常')
        return result

    def poweron_vm(self, vm_name):
        # start poweron task
        si = self._si

        virtualmachine = self.get_obj([vim.VirtualMachine], vm_name)
        try:
            poweron_task = virtualmachine.PowerOnVM_Task()
            wait_for_tasks(si, [poweron_task])
        except vim.fault.InvalidPowerState:
            raise Exception(u"虚拟机电源状态错误")
        return poweron_task.info.state

    def poweroff_vm(self, vm_name):
        si = self._si
        virtualmachine = self.get_obj([vim.VirtualMachine], vm_name)
        try:
            # try shutdown guest task
            virtualmachine.ShutdownGuest()
            return 'success'
        except vim.fault.ToolsUnavailable:
            try:
                poweroff_task = virtualmachine.PowerOffVM_Task()
                wait_for_tasks(si, [poweroff_task])
                return poweroff_task.info.state
            except:
                return 'error'
        except vim.fault.InvalidState:
            return 'success'
        except vim.fault.InvalidPowerState:
            raise Exception(u"虚拟机电源状态错误")
        except:
            return 'error'

    def destroy_vm(self, vm_name):
        si = self._si

        virtualmachine = self.get_obj([vim.VirtualMachine], vm_name)
        try:
            if virtualmachine:
                destroy_task = virtualmachine.Destroy_Task()
            else:
                raise Exception('虚拟机不存在')
            wait_for_tasks(si, [destroy_task])
        except vim.fault.InvalidPowerState:
            raise Exception(u"电源状态异常， 检查是否关闭虚拟机电源！")
        return destroy_task.info.state

    def add_disk(self, virtualmachine, disk_size):
        """
        添加磁盘
        :param disk_size: 磁盘大小
        :return:
        """
        si = self._si
        try:
            config_spec = vim.vm.ConfigSpec()
            # Update VM Devices
            deviceChange = list()
            disk_spec = self.get_disk_spec(virtualmachine, disk_size)
            deviceChange.append(disk_spec)
            config_spec.deviceChange = deviceChange
            add_disk_task = virtualmachine.ReconfigVM_Task(spec=config_spec)
            wait_for_tasks(si, [add_disk_task])
            result = add_disk_task.info.state
        except vim.fault.InvalidPowerState:
            raise Exception(u'虚拟机电源状态异常')
        return result

    def delete_customspec(self, name):
        """
        删除自定义规则
        :param name: 自定义规则name
        """
        content = self._content
        custom_manager = content.customizationSpecManager
        try:
            custom_manager.DeleteCustomizationSpec(name)
        except Exception as e:
            raise e
        else:
            return True

    def get_all_device(self, virtualmachine):
        """
        虚拟机所有设备
        :param virtualmachine:
        :return:
        """
        device = virtualmachine.config.hardware.device
        return device

    def get_available_uint(self, virtualmachine):
        """
        get all disks on a VM, set unit_number to the next available
        :return unit_number
        """
        unit_number = -1
        device = self.get_all_device(virtualmachine)
        for dev in device:
            if hasattr(dev.backing, 'fileName'):
                unit_number = int(dev.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    raise Exception("we don't support this many disks")
        return unit_number

    def get_all_disk(self, virtualmachine):
        """
        获取所有磁盘
        :param virtualmachine:
        :return:
        """
        disks = []
        device = self.get_all_device(virtualmachine)
        for dev in device:
            if hasattr(dev.backing, 'fileName'):
                disks.append(dev)
        return disks

    def get_scsi_controller(self, virtualmachine):
        controller = None
        device = self.get_all_device(virtualmachine)
        for dev in device:
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller = dev
        return controller

    def set_spec_disk(self, disk_size, unit_number, controller, thin_disk=False):
        new_disk_kb = (int(disk_size) * 1024 + 4) * 1024
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        disk_spec.device.backing.thinProvisioned = thin_disk
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        disk_spec.device.controllerKey = controller.key
        return disk_spec

    def get_disk_spec(self, virtualmachine, disk_size):
        """
        """
        unit_number = self.get_available_uint(virtualmachine)
        scsi_controller = self.get_scsi_controller(virtualmachine)
        disk_spec = self.set_spec_disk(disk_size, unit_number, scsi_controller)
        return disk_spec

    def get_network_spec(self, virtualmachine, network):
        """
        """
        network_spec = None
        device = self.get_all_device(virtualmachine)
        for dev in device:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                network_spec = vim.vm.device.VirtualDeviceSpec()
                network_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                network_spec.device = dev
                network_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(
                    network=network, deviceName=network.name)
        return network_spec
