# coding: utf-8
# Author: ld

from collections import defaultdict

from ivmware.api.vmomi import *
# from models import *
from serializers import *
from utils import *
from pyVmomi import vim


class TreeNode(object):
    def __init__(self, data):
        self.data = data
        self.children = list()

    def get_children(self):
        return self.children

    def add_node(self, node):
        self.children.append(node)

    def go(self, data):
        for child in self.children:
            if child.data == data:
                return child
        return None


class Tree:
    def __init__(self, root_node):
        self._root = root_node

    def search(self, path):
        current = self._root
        for step in path:
            if current.go(step) == None:
                return None
            current.go(step)
        return current

    def dfs(self, root, path=tuple()):
        if not len(root.children):
            path += (root.data,)
            yield path
        else:
            for childrens in root.children:
                for p in self.dfs(childrens, path + (root.data,)):
                    yield p

    def get_path_list(self):
        path_list = list(self.dfs(self._root))
        return path_list


class CalcServer(object):
    """
    vmware资源供应服务计算
    """

    def __init__(self, vc_ip=None, vc_user=None, vc_passwd=None, vc_port=443):
        self.vc_ip = vc_ip
        self.vc_user = vc_user
        self.vc_passwd = vc_passwd
        self.vc_port = vc_port
        self.vim_api = VimTasks(self.vc_ip, self.vc_port, self.vc_user, self.vc_passwd)

    def resp_data(self, **kwargs):
        """
        供应参数推荐返回值
        :param kwargs:
        :return:
        """
        result = dict(kwargs)
        result.update(vcenter=self.vc_ip)
        return result

    def ip_recommend(self, network_name):
        ipaddr = None
        network_obj = NetworkResp.objects.get(name=network_name)
        ipusage_set = network_obj.ipusage.filter(occupy=False, ping=False, use=None)
        if ipusage_set.exists():
            ipaddr = ipusage_set.first()
        return ipaddr

    # # vmware资源生成树
    # def resource_tree(self, vc_ip):
    #     vCenter_node = TreeNode(dict(vc_ip=vc_ip))
    #     all_dc = self.vim_api.all_datacenter()
    #     for dc in all_dc:
    #         datacenter_node = TreeNode(dict(datacenter_name=dc.name))
    #         vCenter_node.add_node(datacenter_node)
    #
    #         all_cluster = self.vim_api.cluster_of_datacenter(dc)
    #         for cluster in all_cluster:
    #             cluster_node = TreeNode(dict(cluster_name=cluster.name))
    #             datacenter_node.add_node(cluster_node)
    #
    #             all_host = self.vim_api.host_of_cluster(cluster)
    #             for host in all_host:
    #                 host_data = HostSystemSerializer(host, detail=True).data
    #                 host_usage_mem = host_data.get('usage_mem')
    #                 host_node = TreeNode(dict(hostsystem_name=host.name + '(' + "内存使用率" + str(host_usage_mem) + ')'))
    #                 cluster_node.add_node(host_node)
    #
    #                 all_network = host.network
    #                 for net in all_network:
    #                     network_node = TreeNode(dict(network_name=net.name))
    #                     host_node.add_node(network_node)
    #
    #                     all_datastore = host.datastore
    #                     for store in all_datastore:
    #                         store_data = DataStoreSerializer(store, detail=True).data
    #                         store_usage_space = store_data.get('usage_space')
    #                         datastore_node = TreeNode(
    #                             dict(store_name=host.name + '(' + "空间使用率" + str(store_usage_space) + ')'))
    #                         network_node.add_node(datastore_node)
    #     return vCenter_node

    # vmware资源供应推荐
    def vmware_resource_recommend(self, net):
        result = dict()
        network_name = None
        # 1、检查网络是否存在于所选vc
        network_vimobj = None
        all_networks = self.vim_api.network_of_all()
        net = net.split('/')[0]
        for network in all_networks:
            if net == network.name.split('-')[-1]:
                network_name = network.name
                network_vimobj = network
                break
        if not network_vimobj:
            return
        result.update(network_name=network_name)

        # 2、获取推荐主机(内存最优)
        hostsystems = network_vimobj.host
        if not hostsystems:
            return
        best_host = HostSystemSerializer.get_best_host_of_mb(hostsystems)
        best_host_name = best_host.name
        result.update(hostsystem_name=best_host_name)

        # 3、确定存储
        datastores_of_host = best_host.datastore
        best_datastore = HostSystemSerializer.get_best_datastore_for_host(datastores_of_host)
        best_datastore_name = best_datastore.name

        result.update(datastore_name=best_datastore_name)

        # 4、确定数据中心
        datacenter_vimobj = None
        all_datacenters = self.vim_api.all_datacenter()
        for dc in all_datacenters:
            hostsystems = self.vim_api.host_of_datacenter(dc)
            for host in hostsystems:
                if best_host_name == host.name:
                    datacenter_vimobj = dc
                    break
        if not datacenter_vimobj:
            return
        result.update(datacenter_name=datacenter_vimobj.name)

        # 5、 确定集群
        cluster_vimobj = None
        clusters_of_dc = self.vim_api.cluster_of_datacenter(datacenter_vimobj)
        for cluster in clusters_of_dc:
            hostsystems = self.vim_api.host_of_cluster(cluster)
            for host in hostsystems:
                if best_host_name == host.name:
                    cluster_vimobj = cluster
                    break
        result.update(cluster_name=cluster_vimobj.name)

        return result
