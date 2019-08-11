# coding: utf-8
# Author: ld

"""
此配置文件用于管理蓝图接口列表
"""

from itmsp.settings import LOCAL_HOST, LOCAL_PORT

# 若接口所在后台地址不为本机， 请勿使用itmsp模块配置文件中主机和端口， 需单独拼接成完整url
URL_PREFIX = "http://" + LOCAL_HOST + ":" + LOCAL_PORT

blue_url = [
    # vmware虚拟机基础资源接口
    URL_PREFIX + "/ivmware/clould/server/clone-virtual-machine/",
    URL_PREFIX + "/ivmware/clould/server/reconfigure-virtual-machine/",
    URL_PREFIX + "/ivmware/clould/server/poweron-virtual-machine/",
    URL_PREFIX + "/ivmware/clould/server/poweroff-virtual-machine/",
]

# params_url = [
#     # 参数列表及匹配规则所需接口
#     URL_PREFIX + "/ivmware/clould/server/get-networks/",
#     URL_PREFIX + "/ivmware/clould/server/get-templates/",
# ]
