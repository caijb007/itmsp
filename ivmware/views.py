# coding: utf-8
# Author: ld
"""
虚拟机操作接口
"""
from traceback import format_exc
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from itmsp.settings import REMOTE_LOGDIR
from itmsp.utils.base import smart_get, ping
from itmsp.utils.decorators import post_validated_fields, status, post_data_to_dict
from iuser.permissions import *
from scheduler import *
from .serializers import *
from .tasks import *
from .utils import *
from .api.ansible_v27 import AnsiblePlay
from .ip_pool.utils import build_init_net, avaliable_ip
import ipaddress
import time


@api_view(['POST'])
def test(request):
    ip = avaliable_ip('118.240.13.0/24')
    return Response({"status": 1, "msg": {}, "data": ip})


class NetworkSegmentViewSet(ModelViewSet):
    """
    ip池操作
    """
    queryset = NetworkSegment.objects.all()
    serializer_class = NetworkSegmentSerializer

    @action(detail=False, methods=['post'], url_path='initial-net')
    def initial_net(self, request, *args, **kwargs):
        """
        初始化网段
        """
        msg_prefix = u"初始化网段 "
        req_dict = post_data_to_dict(request.data)
        network = smart_get(req_dict, 'network', str)
        try:
            # 初始化网段
            build_init_net(net=network)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})

    @action(detail=False, methods=['post'], url_path='recommend-ip')
    def recommend_ip(self, request, *args, **kwargs):
        """
        推荐可用ip
        """
        msg_prefix = u"推荐ip "
        req_dict = post_data_to_dict(request.data)
        network = smart_get(req_dict, 'network', str)
        try:
            if not network:
                raise Exception(u"请输入网段")
            build_init_net(network)
            avaliable_ipaddr = avaliable_ip(network)
            ping_status = ping(host=avaliable_ipaddr)
            if ping_status:
                avaliable_ipaddr = None
            unlock_ip.delay(avaliable_ipaddr, time.time(), 1 * 30)  # 锁定30秒

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {"avaliable_ipaddr": avaliable_ipaddr}})


class IPUsageViewSet(ModelViewSet):
    """
    ip池操作
    """
    queryset = IPUsage.objects.all()
    serializer_class = IPUsageSerializer


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['param_id', 'matching_param_value_id', 'param_matching_pattern'])
def get_params_http(request):
    """
    参数推荐
    - 获取参数推荐列表(vc, network, template ...)
    *参数
    ** param_id, 查询参数id, str
    ** matching_param, 匹配项, str
    ** param_matching_pattern, 匹配条件, str
    *返回值
    ** resp, 返回的请求数据, json
    """
    msg_prefix = u"获取参数推荐列表 "
    token = request.META.get('HTTP_AUTHORIZATION')
    try:
        resp = http_get_params(data=request.data, token=token)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        response = Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return response
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": resp})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd'])
def get_datacenter(request):
    """
    & 数据中心
    - 获取数据中心列表
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** detail, 是否显示详细信息, bool
    *返回值
    ***datacenter_moid, 数据中心moid列表, str
    """
    msg_prefix = u"获取数据中心列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)

    detail = smart_get(req_dict, 'detail', bool, True)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        datacenter = vim_api.all_datacenter()
        serializer = DatacenterSerializer(datacenter, detail=detail)

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        response = Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return response
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'datacenter_name'])
def get_cluster(request):
    """
    & 数据中心所有集群
    - 获取数据中心集群列表
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** datacenter_name, 数据中心名, str
    ** detail, 显示详细信息, bool
    *返回值
    *** cluster, 集群列表, list
    """
    msg_prefix = u"获取集群列表 "
    req_dict = post_data_to_dict(request.data)

    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)

    datacenter_name = smart_get(req_dict, 'datacenter_name', str)
    detail = smart_get(req_dict, 'detail', bool, False)

    try:
        data = list()
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        datacenter = vim_api.get_obj(name=datacenter_name)

        if datacenter:
            clusters = vim_api.cluster_of_datacenter(datacenter)
            serializer = ClusterSerializer(clusters, detail=detail)
            data = serializer.data
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'cluster_name'])
def get_cluster_hosts(request):
    """
    & 集群中主机
    - 获取集群中主机列表
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** cluster_name, 集群名, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取集群主机列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)

    cluster_name = smart_get(req_dict, 'cluster_name', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        data = list()
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        cluster = vim_api.get_obj(name=cluster_name)
        if cluster:
            hostsystems = vim_api.host_of_cluster(cluster)
            serializer = HostSystemSerializer(hostsystems, detail=detail)
            data = serializer.data
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'hostsystem_name'])
def get_host_network(request):
    """
    获取主机网络列表(匹配环境)
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** hostsystem_name, 主机名, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取主机网络列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    hostsystem_name = smart_get(req_dict, 'hostsystem_name', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        data = list()
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        hostsystem = vim_api.get_obj(name=hostsystem_name)
        if hostsystem:
            networks = vim_api.network_of_host(hostsystem)
            serializer = NetworkSerializer(networks, detail=detail)
            data = serializer.data
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'hostsystem_name'])
def get_host_datastore(request):
    """
    获取主机存储列表
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** hostsystem_name, 主机名, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取主机存储列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    hostsystem_name = smart_get(req_dict, 'hostsystem_name', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        data = list()
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        hostsystem = vim_api.get_obj(name=hostsystem_name)
        if hostsystem:
            datastores = vim_api.datastore_of_host(hostsystem)
            serializer = DataStoreSerializer(datastores, detail=detail)
            data = serializer.data
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd'])
def get_templates(request):
    """
    获取数据中心模板列表
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** detail, 是否显示详细信息, bool
    """
    msg_prefix = u"获取数据中心模板列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    detail = smart_get(req_dict, 'detail', bool, True)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        templates = vim_api.get_template()
        serializer = VirtualMachineSerializer(templates, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['network'])
def network_recommend(request):
    """
    获取推荐网络信息
    *参数
    ** network, 网段, str
    ** exist_vm_ip, 已推荐的ip, list
    """
    msg_prefix = u"获取推荐网络信息 "
    req_dict = post_data_to_dict(request.data)
    network = smart_get(req_dict, 'network', str)
    try:
        token = request.META.get('HTTP_AUTHORIZATION')
        is_network = network.find('/')
        if is_network == -1:
            raise Exception(u"请检查网络格式")
        # 默认网关
        ip_network = ipaddress.ip_network(unicode(network))
        ip_addrs = [str(i) for i in list(ip_network.hosts())]
        default_gateway = ip_addrs[-1]
        # 掩码
        hostmask = ip_network.netmask.exploded
        # avaliable_ipaddr
        avaliable_ipaddr = get_avaliable_ip(network, token)
        data = dict(
            gateway=default_gateway,
            hostmask=hostmask,
            ipaddress=avaliable_ipaddr
        )
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['ipaddress'])
def ping_ip(request):
    """
    & ip是否能ping通
    * 参数
    ** ipaddr, ip地址, str
    * 返回值
    *** state, 状态, bool
    """
    msg_prefix = u"ip 连接测试 "
    req_dict = post_data_to_dict(request.data)
    ipaddress = req_dict.pop('ipaddress')

    try:
        state = ping(host=ipaddress)
        data = dict(
            state=state
        )
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response(
            {"status": 0, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(
    require=['vc_ip', 'vc_user', 'vc_passwd', 'net', 'env_type', 'unit', 'application', 'node_type'])
def vc_resource_recommend(request):
    """
    & vmware资源供应参数推荐
    - 获取vmware虚拟机申请推荐参数
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vc_port, vcenter连接端口, int
    ** env_type, 环境类型, str
    ** net, 虚拟机网段, str
    ** unit, 所属单位, str
    ** application, 应用程序, str
    ** node_type, 节点类型, str
    ** exist_names, 虚拟机名称缓存, str

    * 返回值
    *** datacenter_name, 数据中心名, str
    *** network_name, 网络名, str
    *** cluster_name, 集群名, str
    *** hostsystem_name, 虚主机名, str
    *** datastore_name, 存储名, str
    *** vm_name, 虚拟机名, str
    """
    msg_prefix = u"vmware资源供应参数推荐 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    env_type = smart_get(req_dict, 'env_type', str)
    net = smart_get(req_dict, 'net', str)
    unit = smart_get(req_dict, 'unit', str)
    application = smart_get(req_dict, 'application', str)
    node_type = smart_get(req_dict, 'node_type', str)
    exist_names = smart_get(req_dict, 'exist_names', list)

    try:
        token = request.META.get('HTTP_AUTHORIZATION')
        calc_server = CalcServer(vc_ip=vc_ip, vc_user=vc_user, vc_passwd=vc_passwd, vc_port=vc_port)
        result = calc_server.vmware_resource_recommend(net)

        vc_info_list = vc_info(token=token)
        vm_name_list = list()
        for vc in vc_info_list:
            vim_api = VimBase(vc['vc_ip'], 443, vc['vc_user'], vc['vc_passwd'])
            virtualmachines = vim_api.get_virtualmachines()
            for vm in virtualmachines:
                vm_name_list.append(vm.name)

        default_name = default_vm_name(env_type, unit, application, node_type, exist_names, vm_name_list)
        result.update(vm_name=default_name)

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": result})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name', 'vm_ip', 'datastore_name', 'cluster_name',
                                'datacenter_name', 'template_name', 'hostsystem_name', 'network'])
def prod_virtual_machine(request):
    """
    & 生成虚拟机
    - 生成虚拟机
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    ** vm_ip, 虚拟机ip, str
    ** datastore_name, 虚拟机存储名, str
    ** cluster_name, 虚拟机所属集群名, str
    ** datacenter_name, 虚拟机所属数据中心名, str
    ** template_name, 虚拟机所用模板名, str
    ** hostsystem_name, 虚拟机所属主机名, str
    ** gateway, 网关, str
    ** subnetMask, 掩码, str
    ** dns, dns, str

    ** apply_user, 负责人, str
    ** node_type, 节点类型, str
    ** application, 应用名称, str
    ** env_type, 环境类型, str
    ** expiration, 过期时间, str
    ** network, 虚拟机网络, str
    ** target_cpu_cores, cpu核心, int
    ** target_mem_gb, 内存大小, int
    ** add_datadisk_gb, 新增硬盘大小, int
    * 返回值
    *** status, success/error, str
    """
    msg_prefix = "克隆虚拟机 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    vm_name = smart_get(req_dict, 'vm_name', str)
    vm_ip = smart_get(req_dict, 'vm_ip', str)
    datastore_name = smart_get(req_dict, 'datastore_name', str)
    cluster_name = smart_get(req_dict, 'cluster_name', str)
    datacenter_name = smart_get(req_dict, 'datacenter_name', str)
    template_name = smart_get(req_dict, 'template_name', str)
    hostsystem_name = smart_get(req_dict, 'hostsystem_name', str)
    gateway = smart_get(req_dict, 'gateway', str)
    subnetMask = smart_get(req_dict, 'subnetMask', str)
    dns = smart_get(req_dict, 'dns', str)

    network = smart_get(req_dict, 'network', str)
    target_cpu_cores = smart_get(req_dict, 'target_cpu_cores', int)
    target_mem_gb = smart_get(req_dict, 'target_mem_gb', int)
    add_datadisk_gb = smart_get(req_dict, 'add_datadisk_gb', int)

    node_type = smart_get(req_dict, 'node_type', str)
    apply_user = smart_get(req_dict, 'apply_user', str)
    env_type = smart_get(req_dict, 'env_type', str)
    expiration = smart_get(req_dict, 'expiration', str)
    application = smart_get(req_dict, 'application', str)

    try:
        if dns:
            dns = dns.split(',')
        kwargs = dict(
            vm_name=vm_name,
            vm_ip=vm_ip,
            datastore_name=datastore_name,
            cluster_name=cluster_name,
            datacenter_name=datacenter_name,
            template_name=template_name,
            hostsystem_name=hostsystem_name,
            gateway=gateway,
            subnetMask=subnetMask,
            dns=dns,

            node_type=node_type,
            apply_user=apply_user,
            env_type=env_type,
            expiration=expiration,
            application=application,
            network=network,
            target_cpu_cores=target_cpu_cores,
            target_mem_gb=target_mem_gb,
            add_datadisk_gb=add_datadisk_gb,
        )

        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        result = vim_api.prod_vm(**kwargs)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        response = Response({"status": 1, "msg": msg, "data": result})
        return response


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name', 'vm_ip', 'datastore_name', 'cluster_name',
                                'datacenter_name', 'template_name', 'hostsystem_name'])
def clone_virtual_machine(request):
    """
    & 克隆虚拟机
    - 克隆虚拟机
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    ** vm_ip, 虚拟机ip, str
    ** datastore_name, 虚拟机存储名, str
    ** cluster_name, 虚拟机所属集群名, str
    ** datacenter_name, 虚拟机所属数据中心名, str
    ** template_name, 虚拟机所用模板名, str
    ** hostsystem_name, 虚拟机所属主机名, str
    ** gateway, 网关, str
    ** subnetMask, 掩码, str
    ** dns, dns, str
    * 返回值
    *** status, success/error, str
    """
    msg_prefix = "克隆虚拟机 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    vm_name = smart_get(req_dict, 'vm_name', str)
    vm_ip = smart_get(req_dict, 'vm_ip', str)
    datastore_name = smart_get(req_dict, 'datastore_name', str)
    cluster_name = smart_get(req_dict, 'cluster_name', str)
    datacenter_name = smart_get(req_dict, 'datacenter_name', str)
    template_name = smart_get(req_dict, 'template_name', str)
    hostsystem_name = smart_get(req_dict, 'hostsystem_name', str)
    gateway = smart_get(req_dict, 'gateway', str)
    subnetMask = smart_get(req_dict, 'subnetMask', str)
    dns = smart_get(req_dict, 'dns', str)

    print '-' * 40 + "clone" + '-' * 40
    print req_dict
    print '-' * 100

    try:
        kwargs = dict(
            vm_name=vm_name,
            vm_ip=vm_ip,
            datastore_name=datastore_name,
            cluster_name=cluster_name,
            datacenter_name=datacenter_name,
            template_name=template_name,
            hostsystem_name=hostsystem_name,
            gateway=gateway,
            subnetMask=subnetMask,
            dns=dns,
        )
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        result = vim_api.clone_vm(**kwargs)
        data = dict(
            status=result
        )
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        response = Response({"status": 1, "msg": msg, "data": data})
        return response


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name'])
def reconfigure_virtual_machine(request):
    """
    & 配置虚拟机
    - 配置虚拟机
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    ** network, 虚拟机网络, str
    ** apply_user, 负责人, str
    ** node_type, 节点类型, str
    ** application, 应用名称, str
    ** env_type, 环境类型, str
    ** expiration, 过期时间, str
    ** target_cpu_cores, cpu核心, int
    ** target_mem_gb, 内存大小, int
    ** add_datadisk_gb, 新增硬盘大小, int
    * 返回值
    *** status, success/error, str
    """
    msg_prefix = "配置虚拟机 "
    req_dict = post_data_to_dict(request.data)
    print '-' * 40 + "reconfigure" + '-' * 40
    print req_dict
    print '-' * 100
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    vm_name = smart_get(req_dict, 'vm_name', str)
    network = smart_get(req_dict, 'network', str)
    target_cpu_cores = smart_get(req_dict, 'target_cpu_cores', int)
    target_mem_gb = smart_get(req_dict, 'target_mem_gb', int)
    add_datadisk_gb = smart_get(req_dict, 'add_datadisk_gb', int)
    node_type = smart_get(req_dict, 'node_type', str, '')
    apply_user = smart_get(req_dict, 'apply_user', str, '')
    env_type = smart_get(req_dict, 'env_type', str, '')
    expiration = smart_get(req_dict, 'expiration', str, '')
    application = smart_get(req_dict, 'application', str, '')

    kwargs = dict(
        vm_name=vm_name,
        network=network,
        target_cpu_cores=target_cpu_cores,
        target_mem_gb=target_mem_gb,
        add_datadisk_gb=add_datadisk_gb,
        node_type=node_type,
        apply_user=apply_user,
        env_type=env_type,
        expiration=expiration,
        application=application,
    )
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        result = vim_api.reconfig_vm(**kwargs)
        data = dict(
            status=result
        )
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        response = Response({"status": 1, "msg": msg, "data": data})
        return response


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name'])
def poweron_virtual_machine(request):
    """
    & 开机
    - 开机
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    * 返回值
    *** status, success/error, str
    """
    msg_prefix = "开机 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    vm_name = smart_get(req_dict, 'vm_name', str)
    print '-' * 40 + "poweron" + '-' * 40
    print req_dict
    print '-' * 100
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        result = vim_api.poweron_vm(vm_name=vm_name)
        data = dict(
            status=result
        )
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        response = Response({"status": 1, "msg": msg, "data": data})
        return response


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name'])
def poweroff_virtual_machine(request):
    """
    & 关机
    - 关机
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    * 返回值
    *** status, success/error, str
    """
    msg_prefix = "关机 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    vm_name = smart_get(req_dict, 'vm_name', str)

    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        result = vim_api.poweroff_vm(vm_name=vm_name)
        data = dict(
            status=result
        )
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        response = Response({"status": 1, "msg": msg, "data": data})
        return response


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name'])
def destroy_virtual_machine(request):
    """
    & 删除虚拟机
    - 删除虚拟机
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    * 返回
    *** status, success/error, str
    """
    msg_prefix = u"删除虚拟机 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    vm_name = smart_get(req_dict, 'vm_name', str)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        result = vim_api.destroy_vm(vm_name=vm_name)
        data = dict(
            status=result
        )
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": data})


#
# @api_view(['POST'])
# # @permission_classes((require_menu(["I00301"]),))
# @post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name'])
# def search(request):
#     """
#     - 搜索虚拟机
#     * 参数
#     ** vc_ip, vcenter ip, str
#     ** vc_user, vcenter用户名, str
#     ** vc_passwd, vcenter用户密码, str
#     ** vm_name, 虚拟机名, str
#     * 返回
#     *** status, success/error, str
#     """
#     msg_prefix = u"搜索虚拟机 "
#     req_dict = post_data_to_dict(request.data)
#     vc_ip = smart_get(req_dict, 'vc_ip', str)
#     vc_user = smart_get(req_dict, 'vc_user', str)
#     vc_port = smart_get(req_dict, 'vc_port', int, 443)
#     vc_passwd = smart_get(req_dict, 'vc_passwd', str)
#     vm_name = smart_get(req_dict, 'vm_name', str)
#     try:
#         if not vm_name:
#             raise Exception(u"请填写虚拟机名")
#         vm_name_list = list()
#         result = False
#         vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
#         vm_list = vim_api.get_virtualmachines()
#         for vm in vm_list:
#             vm_name_list.append(vm.name)
#         if vm_name in vm_name_list:
#             result = True
#
#         data = dict(
#             result=result
#         )
#     except Exception, e:
#         msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
#         logger.error(format_exc())
#         return Response({"status": -1, "msg": msg, "data": {}},
#                         status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     else:
#         msg = msg_prefix + u"成功!"
#         return Response({"status": 0, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vm_name'])
def search_vm_name(request):
    """
    - 搜索虚拟机名
    """
    msg_prefix = u"搜索虚拟机名 "
    req_dict = post_data_to_dict(request.data)
    vm_name = smart_get(req_dict, 'vm_name', str)
    try:
        is_exist = False
        authorization = request.META.get('HTTP_AUTHORIZATION')
        vc_info_list = vc_info(token=authorization)
        vm_name_list = list()
        for vc in vc_info_list:
            vim_api = VimBase(vc[VC_IP], 443, vc[VC_USER], vc[VC_PASSWD])
            virtualmachines = vim_api.get_virtualmachines()
            for vm in virtualmachines:
                vm_name_list.append(vm.name)

        if vm_name in vm_name_list:
            is_exist = True

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": is_exist})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'cluster_name'])
def get_best_hosts(request):
    """
    smart
    & 主机
    - 获取集群中最优主机
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** cluster_name, 集群名, str
    ** detail, 显示详细信息, bool
    *返回值
    *** hostsystem_name, 最优主机名, str
    """
    msg_prefix = u"获取集群最优主机 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    cluster_name = smart_get(req_dict, 'cluster_name', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        cluster = vim_api.get_obj(name=cluster_name)
        cluster_serializer = ClusterSerializer(cluster)

        best_host = cluster_serializer.best_host_of_mb
        serializer = HostSystemSerializer(best_host, detail=detail)

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'cluster_name'])
def get_cluster_resp(request):
    """
    获取集群关联资源池列表
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** cluster_name, 集群名, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取集群资源池列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    cluster_name = smart_get(req_dict, 'cluster_name', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        cluster = vim_api.get_obj(name=cluster_name)
        resp = vim_api.resp_of_cluster(cluster)
        serializer = ResourcePoolSerializer(resp, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


##############################################分割线#################################################################

@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name'])
def get_vm_by_dnsname(request):
    """
    & 由dns名查找虚拟机
    - 由dns名查找虚拟机
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"搜索虚拟机 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = req_dict.pop('vc_ip')
    vc_user = req_dict.pop('vc_user')
    vc_passwd = req_dict.pop('vc_passwd')
    vc_port = req_dict.pop('vc_port', 443)
    vm_name = smart_get(req_dict, 'vm_name', str)

    detail = smart_get(req_dict, 'detail', bool, True)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        virtualmachines = vim_api.findvm_by_dnsname(vm_name=vm_name)
        serializer = VirtualMachineSerializer(virtualmachines, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'ipaddress'])
def get_vm_by_ip(request):
    """
    & 由ip地址查找虚拟机
    - 注 - 虚拟机关机状态不能使用ip查找
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取虚拟机 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = req_dict.pop('vc_ip')
    vc_user = req_dict.pop('vc_user')
    vc_passwd = req_dict.pop('vc_passwd')
    vc_port = req_dict.pop('vc_port', 443)
    ipaddress = smart_get(req_dict, 'ipaddress', str)

    detail = smart_get(req_dict, 'detail', bool, True)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        virtualmachine = vim_api.findvm_by_ip(ip=ipaddress)
        serializer = VirtualMachineSerializer(virtualmachine, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'hostsystem_name'])
def get_best_datastore(request):
    """
    筛选最佳存储(空间占用率最低)
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** hostsystem_name, 主机名, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取主机存储列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    hostsystem_name = smart_get(req_dict, 'hostsystem_name', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        hostsystem = vim_api.get_obj(name=hostsystem_name)
        host_serializer = HostSystemSerializer(hostsystem)
        best_datastore = host_serializer.best_datastore
        serializer = DataStoreSerializer(best_datastore, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd'])
def get_networks(request):
    """
    获取所有网络
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取所有网络 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        networks = vim_api.network_of_all()
        serializer = NetworkSerializer(networks, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'datacenter_name'])
def get_datacenter_network(request):
    """
    获取数据中心所有网络
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** datacenter_name, 数据中心名, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取所有网络 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    datacenter_name = smart_get(req_dict, 'datacenter_name', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        datacenter = vim_api.get_obj(name=datacenter_name)
        networks = vim_api.network_of_datacenter(datacenter)
        serializer = NetworkSerializer(networks, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd'])
def get_virtualmachines(request):
    """
    获取数据中心虚拟机或模板列表
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** datacenter_name, 数据中心名, str
    ** detail, 显示详细信息, bool
    """
    msg_prefix = u"获取虚拟机或模板列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        virtualmachines = vim_api.get_virtualmachines()
        serializer = VirtualMachineSerializer(virtualmachines, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name'])
def get_virtualmachine_info(request):
    """
    获取虚拟机信息
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    """
    msg_prefix = u"获取虚拟机或模板列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    vm_name = smart_get(req_dict, 'vm_name', str)
    try:
        if not vm_name:
            raise Exception(u"请填写虚拟机名")
        vm_obj = None
        vm_info = dict()
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        virtualmachines = vim_api.get_virtualmachines()
        for vm in virtualmachines:
            if vm.name == vm_name:
                vm_obj = vm
        if vm_obj:
            serializer = VirtualMachineSerializer(vm_obj, detail=True)
            vm_info = serializer.data
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": vm_info})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd'])
def get_customspec(request):
    """
    获取自定义规则列表
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** detail - 显示详细信息
    """
    msg_prefix = u"获取自定义规则 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    detail = smart_get(req_dict, 'detail', bool, False)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        customspec = vim_api.all_customspec()
        serializer = CustomSpecSerializer(customspec, detail=detail)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": serializer.data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'spec_name'])
def delete_customspec(request):
    """
    删除自定义规则
    *参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** spec_name, 自定义规则name, str
    """
    msg_prefix = u"删除自定义规则 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = smart_get(req_dict, 'vc_ip', str)
    vc_user = smart_get(req_dict, 'vc_user', str)
    vc_port = smart_get(req_dict, 'vc_port', int, 443)
    vc_passwd = smart_get(req_dict, 'vc_passwd', str)
    spec_name = smart_get(req_dict, 'spec_name', str)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        result = vim_api.delete_customspec(spec_name)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": result})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['env_type', 'unit', 'stock_app', 'internal_app'])
def default_vmware_name(request):
    """
    获取推荐虚拟机名称
    *参数
    ** env_type, 环境类型, str
    ** unit, 单位, str
    ** stock_app, 存量应用, str
    ** internal_app, 分行特色应用, str
    ** exist_names, 虚拟机名称页面缓存, list
    * 返回值
    *** default_name, 默认虚拟机名, str
    """
    msg_prefix = u"获取推荐虚拟机名称 "
    req_dict = post_data_to_dict(request.data)
    env_type = smart_get(req_dict, 'env_type', str)
    unit = smart_get(req_dict, 'unit', str)
    stock_app = smart_get(req_dict, 'stock_app', str)
    internal_app = smart_get(req_dict, 'internal_app', str)
    exist_names = smart_get(req_dict, 'exist_names', list)
    try:
        default_name = default_vm_name(env_type, unit, stock_app, internal_app, exist_names)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 1, "msg": msg, "data": {"default_name": default_name}})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name'])
def get_disk(request):
    """
    获取所有磁盘
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    """
    msg_prefix = u"获取虚拟机磁盘列表 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = req_dict.pop('vc_ip')
    vc_user = req_dict.pop('vc_user')
    vc_passwd = req_dict.pop('vc_passwd')
    vc_port = req_dict.pop('vc_port', 443)
    vm_name = smart_get(req_dict, 'vm_name', str)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        virtualmachines = vim_api.findvm_by_dnsname(vm_name=vm_name)
        disks = vim_api.get_all_disk(virtualmachines)

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response(
            {"status": 0, "msg": msg, "data": str(disks)})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['vc_ip', 'vc_user', 'vc_passwd', 'vm_name', 'disk_size'])
def add_disk(request):
    """
    添加新磁盘
    * 参数
    ** vc_ip, vcenter ip, str
    ** vc_user, vcenter用户名, str
    ** vc_passwd, vcenter用户密码, str
    ** vm_name, 虚拟机名, str
    ** disk_size, 磁盘大小, int
    * 返回值
    ** state, 添加磁盘状态, str
    """
    msg_prefix = u"添加磁盘 "
    req_dict = post_data_to_dict(request.data)
    vc_ip = req_dict.pop('vc_ip')
    vc_user = req_dict.pop('vc_user')
    vc_passwd = req_dict.pop('vc_passwd')
    vc_port = req_dict.pop('vc_port', 443)
    vm_name = smart_get(req_dict, 'vm_name', str)
    disk_size = smart_get(req_dict, 'disk_size', int)
    try:
        vim_api = VimTasks(vc_ip, vc_port, vc_user, vc_passwd)
        virtualmachines = vim_api.findvm_by_dnsname(vm_name=vm_name)
        state = vim_api.add_disk(virtualmachines, disk_size)
        data = {"state": state}
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response(
            {"status": 0, "msg": msg, "data": data})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['host_list', 'conn_user', 'conn_pass', 'local_user', 'become_pass'])
def push_pubkey(request):
    """
    推送用户公钥
    * 参数
    ** ipaddress - 目标ip
    ** conn_user - 远程主机用户
    ** conn_pass - 远程主机用户密码
    ** become_pass - 远程主机sudo密码
    ** local_user - 本地用户
    """
    msg_prefix = u"推送用户公钥 "
    req_dict = post_data_to_dict(request.data)
    host_list = smart_get(req_dict, 'host_list', str)
    conn_user = smart_get(req_dict, 'conn_user', str)
    conn_pass = smart_get(req_dict, 'conn_pass', str)
    become_pass = smart_get(req_dict, 'become_pass', str)
    local_user = smart_get(req_dict, 'local_user', str)
    try:
        ansible_api = AnsiblePlay(host_list, local_user, conn_user, conn_pass, become_pass)
        data = ansible_api.play_authorized_user(conn_user, local_user)
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": {"result": str(data)}})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['ipaddress', 'conn_user', 'auth_type', 'os_type'])
def remove_vg(request):
    """
    删除vg
    * 参数
    ** ipaddress - 目标ip地址
    ** conn_user - 目标用户(此ip上用户)
    ** conn_pass - 目标主机用户密码
    ** become_pass - 目标主机用户sudo密码
    ** local_user - 本地用户(平台账户)
    ** os_type - 操作系统类型
    ** auth_type - 认证方式(pubkey/password)
    ** vg_name - vg_name
    ** disk_path - 磁盘路径
    """
    msg_prefix = u"删除vg "
    req_dict = post_data_to_dict(request.data)
    ipaddress = smart_get(req_dict, 'ipaddress', str)
    conn_user = smart_get(req_dict, 'conn_user', str)
    conn_pass = smart_get(req_dict, 'conn_pass', str)
    local_user = smart_get(req_dict, 'local_user', str)
    become_pass = smart_get(req_dict, 'become_pass', str)
    auth_type = smart_get(req_dict, 'auth_type', str)
    os_type = smart_get(req_dict, 'os_type', str)
    vg_name = smart_get(req_dict, 'vg_name', str, "datavg")
    disk_path = smart_get(req_dict, 'disk_path', str)
    try:
        play = PlayWithAdminUsingPass(ipaddress, conn_user, conn_pass, local_user, become_pass=become_pass)
        readout = play.resize_vg(vg_name, disk_path)

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": str(readout)})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(
    require=['ipaddress', 'conn_user', 'auth_type', 'os_type', 'unit_number', 'conn_pass', 'local_user', 'become_pass'])
def vm_partition(request):
    """
    操作系统分区和添加文件系统
    * 参数
    ** ipaddress - 目标ip地址
    ** conn_user - 目标用户(此ip上用户)
    ** conn_pass - 目标主机用户密码
    ** become_pass - 目标主机用户sudo密码
    ** local_user - 本地用户(平台账户)
    ** os_type - 操作系统类型
    ** auth_type - 认证方式(pubkey/password)
    ** disk_path - 磁盘路径 (默认为 /dev/sd)
    ** unit_number - 磁盘编号
    ** vg_name - vg_name
    """
    msg_prefix = u"操作系统分区和添加文件系统 "
    req_dict = post_data_to_dict(request.data)
    ipaddress = smart_get(req_dict, 'ipaddress', str)
    conn_user = smart_get(req_dict, 'conn_user', str)
    conn_pass = smart_get(req_dict, 'conn_pass', str)
    become_pass = smart_get(req_dict, 'become_pass', str)
    local_user = smart_get(req_dict, 'local_user', str, 'admin')
    auth_type = smart_get(req_dict, 'auth_type', str)
    os_type = smart_get(req_dict, 'os_type', str)
    unit_number = smart_get(req_dict, 'unit_number', int)
    disk_path = smart_get(req_dict, 'disk_path', str, '/dev/sd')
    vg_name = smart_get(req_dict, 'vg_name', str, "datavg")
    try:
        result = None
        if os_type == "Linux":
            disk_path = disk_path + chr(97 + unit_number)
            if disk_path:
                # ssh_executor = SshExecutor(hostname=ipaddress, conn_user=conn_user, conn_pass=conn_pass,
                #                            auth_type=auth_type, local_user=local_user)
                # readout = ssh_executor.add_disk_to_vg(vg_name, disk_path)

                play = PlayWithAdminUsingPass(ipaddress, conn_user, conn_pass, local_user, become_pass)
                # result = play.parted(disk_path)
                result = play.test()
            else:
                raise Exception(u"未找到磁盘！")
        else:
            pass

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": {"result": result}})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['ipaddress', 'conn_user', 'auth_type', 'soft_id'])
def vm_install_soft(request):
    """
    安装软件
    * 参数
    ** ipaddress - 目标ip地址
    ** conn_user - 目标用户(此ip上用户)
    ** conn_pass - 目标主机用户密码
    ** become_pass - 目标主机用户sudo密码
    ** local_user - 本地用户(平台账户)
    ** auth_type - 认证方式(pubkey/passwd)
    ** soft_id - 安装软件id(列表)
    ** install_dir - 软件安装介质本地存放目录(绝对路径)
    ** package_type - 软件包类型
    ** package_name - 软件包名称
    """
    msg_prefix = u"安装软件，任务启动 "
    req_dict = post_data_to_dict(request.data)
    ipaddress = smart_get(req_dict, 'ipaddress', str)
    conn_user = smart_get(req_dict, 'conn_user', str)
    conn_pass = smart_get(req_dict, 'conn_pass', str)
    become_pass = smart_get(req_dict, 'become_pass', str)
    auth_type = smart_get(req_dict, 'auth_type', str)
    local_user = smart_get(req_dict, 'local_user', str)
    install_dir = smart_get(req_dict, 'install_dir', str)
    soft_ids = smart_get(req_dict, 'soft_id', int)

    try:
        software = Software.objects.get(id=soft_ids)
        if software.support_os == 'Linux':
            if software.install_method == "ansible":
                if software.playbook:
                    pass
                else:
                    play = PlayWithAdminUsingPass(ipaddress, conn_user, conn_pass, local_user, become_pass)

                    dirs = [install_dir, REMOTE_LOGDIR]
                    play.create_dir(dirs)
                    run = play.shell_cmd(install_dir, REMOTE_LOGDIR, software.medium_path, software.script_path, 1)

                    # result = play.install_soft(softname=software.name, package_manage=software.package_manage,
                    #                            medium_path=software.medium_path)

            elif software.install_method == "ssh":

                ssh_executor = SshExecutor(hostname=ipaddress, conn_user=conn_user, auth_type=auth_type,
                                           local_user=local_user, conn_pass=conn_pass)
                medium_path = software.medium_path
                script_path = software.script_path
                result = ssh_executor.install_stuff(install_dir, medium_path, script_path)

            elif software.install_method == "dcap":
                pass
        elif software.support_os == 'Windows':
            pass
        else:
            raise Exception(u"不支持的操作系统！")

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": {}})


@api_view(['POST'])
# @permission_classes((require_menu(["I00301"]),))
@post_validated_fields(require=['ipaddress'])
def vm_add_user(request):
    """
    添加管理员用户
    * 参数
    ** ipaddress - 目标ip地址
    """
    msg_prefix = u"添加管理员用户，任务启动 "
    req_dict = post_data_to_dict(request.data)
    ipaddress = smart_get(req_dict, 'ip', str)
    try:
        # play = PlayWithAdmin(ipaddress)
        # play.play_add_user(target_user)
        pass

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = msg_prefix + u"成功!"
        return Response({"status": 0, "msg": msg, "data": {}})

# @api_view(['POST'])
# @permission_classes((require_menu(["I00302", "I00303", "I00304"]),))
# @post_validated_fields(require=['id'])
# def vm_mail_notice(request):
#     """
#     邮件通知申请人/审批人
#     :param request:
#     :return:
#     """
#     msg_prefix = u"邮件通知 "
#     req_dict = post_data_to_dict(request.data)
#     id = smart_get(req_dict, 'id', int)
#     try:
#         if not ipaddress:
#             virtualmachine = VirtualMachine.objects.get(id=id)
#             vcenter = virtualmachine.resourcepool.vcenter
#             ipaddress = get_vm_ip(virtualmachine)
#
#         subject = DEFAULT_SUBJECT_PREFIX + u"虚拟环境资源信息"
#         content = (u"虚拟环境资源[{vm_name}]生成完毕，附资源详情信息，请知晓。\n\n" +
#                    u"资源详情:\n" +
#                    u"\t资源名称: {vm_name}\n" +
#                    u"\tIP 地址:  {vm_ip}\n" +
#                    "").format(
#             vm_name=virtualmachine.name, os=virtualmachine.guestos_fullname,
#             vm_ip=", ".join([ip for ip in ipaddress]),
#         )
#         to = [approval.applicant.email]
#         cc = [approval.approver.email]
#         # 生产环境直接调内部接口
#         send_single_mail(subject=subject, content=content, to=to, cc=cc)
#
#
#     except Exception, e:
#         msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
#         logger.error(format_exc())
#         return Response({"status": -1, "msg": msg, "data": {}},
#                         status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     else:
#         msg = msg_prefix + u"成功!"
#         return Response({"status": 0, "msg": msg_prefix, "data": {}})
