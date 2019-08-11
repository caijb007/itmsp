# coding: utf-8
# Author: ld

from ..models import IPUsage, NetworkSegment
from itmsp.utils.base import ping
from threading import Thread
import subprocess
import ipaddress
import Queue
import time

MAX_THREAD = 500


class ThreadPing(object):
    """
    并发ping网段
    """

    def __init__(self, data_list):
        self._sentinel = object()
        self.data_list = data_list
        self.t_num = 200

    def producer(self, out_q):
        while self.data_list:
            out_q.put(self.data_list.pop())
        out_q.put(self._sentinel)

    def consumer(self, in_q):
        while not in_q.empty():
            host = in_q.get()
            if host is self._sentinel:
                in_q.put(self._sentinel)
            else:
                status = ping(host=host)
                change_status_ipusage(host, status)
            in_q.task_done()

    def run(self):
        start = time.time()
        q = Queue.Queue()
        p = Thread(target=self.producer, args=(q,))
        p.daemon = True
        p.start()
        print len(self.data_list)
        for i in range(len(self.data_list)):
            # for i in range(self.t_num):
            t = Thread(target=self.consumer, args=(q,))
            t.daemon = True
            t.start()
        return time.time() - start


def change_status_ipusage(host, status):
    """
    根据ping结果修改ip状态:
    """
    print "change_status_ipusage--", host
    ipusage_set = IPUsage.objects.filter(ipaddress=host)
    if len(ipusage_set):
        ipusage = ipusage_set[0]
        ipusage.is_ping = True if status else False
        ipusage.is_avaliable = False if status or ipusage.is_occupy else True
        ipusage.save()
    return


def ping_ips(ip_ipaddrs):
    """
    批量ping
    """
    print "ping_ips"
    thread_ping = ThreadPing(ip_ipaddrs)
    thread_ping.run()


def init_net(network):
    """
    初始化网络
    """
    i_net = unicode(network.net) + u'/' + unicode(network.netmask)
    ip_network = ipaddress.ip_network(i_net)
    ip_ipaddrs = [str(i) for i in list(ip_network.hosts())]
    for ip in ip_ipaddrs:
        ipusage_set = IPUsage.objects.filter(ipaddress=ip)
        if not len(ipusage_set):
            IPUsage.objects.create(network_id=network.id, ipaddress=ip)
    print "init_net"
    return ip_ipaddrs


def build_init_net(net):
    """
    网段是否初始化
    是：pass
    否：初始化网段
    """
    n_net = net.split('/')[0]
    n_netmask = net.split('/')[-1]
    network = NetworkSegment.objects.filter(net=n_net).last()
    if not network:
        # 创建网段数据库记录
        network, created = NetworkSegment.objects.get_or_create(net=n_net, netmask=n_netmask)
    if not network.inited:
        print 'build_init_net'
        ip_ipaddrs = init_net(network)
        ping_ips(ip_ipaddrs)
    network.inited = True
    network.save()


def avaliable_ip(net):
    net = net.split('/')[0]
    avaliable_ipusage = IPUsage.objects.filter(network__net=net, is_avaliable=True, is_lock=False, is_ping=False)
    if not avaliable_ipusage:
        raise Exception(u"该网段ip资源告罄, 请联系管理员")
    default_avaliable_ipusage = avaliable_ipusage[0]
    default_ip = default_avaliable_ipusage.ipaddress
    status = ping(default_ip)
    change_status_ipusage(default_ip, status)
    if status:
        avaliable_ip(net)
    default_avaliable_ipusage.is_lock = True
    default_avaliable_ipusage.save()
    return default_ip
