# coding: utf-8
# Author: Dunkle Qiu

from itmsp.settings import IVM
from itmsp.models import DataDict
from iuser.models import ExGroup


class EnvType(object):
    def __init__(self):
        self.set = DataDict.options.get_options('ivmware', 'env_type')
        self.value = [option.value for option in self.set]

    def get_dict(self, env_list=list()):
        env_type_dict = {}
        for val in self.value:
            env_type_dict[val] = val in env_list
        return env_type_dict

    def get_prefix(self, env_type):
        return self.set.get(value=env_type).ext_attr.get(IVM['VM_PREFIX_KEY'])


class OsVersion(object):
    def __init__(self):
        self.set = DataDict.options.get_options('ivmware', 'os_version')
        self.value = [option.value for option in self.set]


class DataCenter(object):
    def __init__(self):
        self.set = DataDict.options.get_options('ivmware', 'datacenter')
        # self.value = [option.value for option in self.set]
        self.mapping = {
            option.ext_attr['ip_pattern']: option.ext_attr[IVM['VM_PREFIX_KEY']] for option in self.set
        }

    def get_prefix(self, ipaddress):
        for k, v in self.mapping.items():
            if ipaddress.find(k) == 0:
                return v
        raise Exception(u"找不到匹配值")
