# # coding: utf-8
# # Author: ld
#
# from itmsp.utils.base import ping
# from itmsp.celery import app
# from ..models import IPUsage
# from .utils import change_status_ipuaage
# import time
#
#
# @app.tasks
# def unlock_ip(ipaddr, after_time):
#     """
#     解锁ip
#     """
#     ipusage = IPUsage.objects.get(ipaddress=ipaddr)
#     try:
#         ping_status = ping(host=ipaddr)
#         if ping_status:
#             change_status_ipuaage(ipaddr, ping_status)
#             ipusage.is_lock = False
#             ipusage.save()
#             return
#         time.sleep(after_time)
#     finally:
#         ping_status = ping(host=ipaddr)
#         change_status_ipuaage(ipaddr, ping_status)
#         ipusage.is_lock = False
#         ipusage.save()
