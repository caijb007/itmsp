# coding: utf-8
# Author: ld

from itmsp.utils.base import ping
from itmsp.celery import app
from .models import IPUsage, NetworkSegment
from .ip_pool.utils import change_status_ipusage, ping_ips
import time
import ipaddress


@app.task()
def unlock_ip(ipaddr, accept_time, locak_time):
    """
    解锁ip
    """
    current_time = time.time()
    after_time = current_time - accept_time

    ipusage = IPUsage.objects.get(ipaddress=ipaddr)
    ping_status = ping(host=ipaddr)
    if ping_status:
        change_status_ipusage(ipaddr, ping_status)
        ipusage.is_lock = False
        ipusage.save()
        return True

    if after_time < locak_time:
        time.sleep(locak_time - after_time)
        unlock_ip(ipaddr, accept_time, locak_time)


@app.task()
def sync_network():
    """
    同步网络连接情况
    """
    network_set = NetworkSegment.objects.all()
    network_list = [unicode(network.net) + '/' + unicode(network.netmask) for network in network_set]
    ip_addrs_list = list()
    for network in network_list:
        ip_network = ipaddress.ip_network(network)
        ip_ipaddrs = [str(i) for i in list(ip_network.hosts())]
        ip_addrs_list += ip_ipaddrs
    ping_ips(ip_addrs_list)
