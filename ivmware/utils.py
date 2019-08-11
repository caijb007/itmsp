# coding: utf-8
# Author: ld
from itmsp.settings import IVM, LOCAL_HOST, LOCAL_PORT
import requests
import json
import re

VC_IP = "vc_ip"
VC_USER = "vc_user"
VC_PASSWD = "vc_passwd"
SERVER_ADDR = 'http://' + LOCAL_HOST + ":" + LOCAL_PORT


def default_vm_name(env_type, unit, stock_app, internal_app, exist_names, vm_name_list):
    """
    :param env_type: 环境类型
    :param unit: 单位
    :param stock_app: 存量应用
    :param internal_app: 分行特色应用
    :param exist_names: 虚拟机名称页面缓存
    :return: 虚拟机名
    """
    # 组合默认前缀名
    one_env_type = env_type[0].lower()
    if len(unit) != 4:
        return None
    four_unit = unit[:4].lower()

    stock_app = re.sub(r'[\s\n]', '', stock_app)
    stock_app = stock_app.split('-')[-1].split('(')[0]

    if len(stock_app) < 4:
        stock_app = 'f' + stock_app
    four_stock_app = stock_app[:4].lower()
    three_internal_app = internal_app[:3].lower()
    prefix_name = one_env_type + four_unit + four_stock_app + three_internal_app
    # 已经存在的前缀名集合， 用于统计当前审批已存在虚拟机数量
    exist_name_list = list()

    for vm_name in vm_name_list:
        exist_name_list.append(vm_name)

    # 页面缓存虚拟机名
    for exist_name in exist_names:
        exist_name_list.append(exist_name)

    # 与所申请前缀相同的虚拟机名集合
    prefix_in_name = [i for i in exist_name_list if prefix_name in i]

    # 过滤出前缀集合
    exist_prefix_names = [last_three_name[-3:] for last_three_name in prefix_in_name]

    # 找出最大数　+1
    number = 1
    if exist_prefix_names:
        exist_prefix_names = [int(i) for i in exist_prefix_names]
        number = max(exist_prefix_names) + 1

    # 表述为字符串
    three_numbre = "%03d" % number
    # 拼接全部名称
    default_name = prefix_name + three_numbre
    return default_name


def http_get_params(data=None, token=None):
    server_addr = 'http://' + LOCAL_HOST + ":" + LOCAL_PORT
    path = "/icatalog/server-param-matching-condition/obtain-matching-rule-values/"
    url = server_addr + path
    headers = {'Content-Type': 'application/json', 'Authorization': token}
    json_data = json.dumps(data)
    r = requests.post(url=url, data=json_data, headers=headers)
    return r.json()


def annotation_to_dict(annotation):
    """
    vc注解转行成字典(带换行符)
    """
    data = re.split(r'[\n]', annotation)
    if not data:
        return False

    # 去除空行
    annotation_lines = list()
    for desc in data:
        if len(desc):
            if desc.find(':') == -1:  # 非itmsp自动生成格式
                return False
            annotation_lines.append(desc)
    annotation_dict = dict()
    for annotation_line in annotation_lines:
        annotation_line = re.sub(r'[\s\n]', '', annotation_line)  # 去除空白字符
        annotation_dict[annotation_line.split(':')[0]] = annotation_line.split(':')[-1]

    return annotation_dict


def dict_to_annotation(dict_annotation):
    """
    由字典转换为注解格式(字符串)
    """
    annotation_lines = list()
    title = dict_annotation.pop('title')
    str_title = unicode("title") + ':' + unicode(title) + unicode('\r\n')
    annotation_lines.append(str_title)
    for k, v in dict_annotation.items():
        string = unicode(k) + ':' + unicode(v) + unicode('\r\n')
        annotation_lines.append(string)

    annotation = unicode()
    for annotation_line in annotation_lines:
        annotation += annotation_line
    return annotation


def annotation_format(annotation, apply_user='', node_type='', application='', env_type='',
                      expiration=''):
    """
    vm注解转换
    """
    # 首次设置
    if not annotation:
        annotation = dict(
            title=u"该资源由itmsp自动生成",
            apply_user=apply_user,
            node_type=node_type,
            application=application,
            env_type=env_type,
            expiration=expiration
        )
    # 再次设置
    else:
        try:
            annotation = annotation_to_dict(annotation)
            if annotation:
                # 转换字典
                # annotation = json.loads(annotation)
                if apply_user:
                    annotation['apply_user'] = unicode(apply_user)
                if node_type:
                    annotation['node_type'] = unicode(node_type)
                if application:
                    annotation['application'] = unicode(application)
                if env_type:
                    annotation['env_type'] = unicode(env_type)
                if expiration:
                    annotation['expiration'] = unicode(expiration)
            else:
                # 存在旧注解
                annotation = dict(
                    title=u"该注解由itmsp自动生成",
                    backup=unicode(annotation),  # 整体备份
                    apply_user=unicode(apply_user),
                    node_type=unicode(node_type),
                    application=unicode(application),
                    env_type=unicode(env_type),
                    expiration=unicode(expiration)
                )
        except ValueError:
            # 存在旧注解
            annotation = dict(
                title=u"该注解由itmsp自动生成",
                backup=unicode(annotation),  # 整体备份
                apply_user=unicode(apply_user),
                node_type=unicode(node_type),
                application=unicode(application),
                env_type=unicode(env_type),
                expiration=unicode(expiration)
            )
    annotation = dict_to_annotation(annotation)
    return annotation


def vc_info(token):
    """
    获取所有vcenter账号信息
    :param token: 请求携带的token
    :return: vcenter账号信息列表
    """
    path = "/icatalog/server-params_value/get-param-values-list/"
    url = SERVER_ADDR + path
    headers = {'Content-Type': 'application/json', 'Authorization': token}

    vc_ip_req = json.dumps({"param_name": VC_IP})
    vc_ip_res = requests.post(url=url, data=vc_ip_req, headers=headers)
    vc_ip_list = vc_ip_res.json()

    vc_user_req = json.dumps({"param_name": VC_USER})
    vc_user_res = requests.post(url=url, data=vc_user_req, headers=headers)
    vc_user_list = vc_user_res.json()

    vc_passwd_req = json.dumps({"param_name": VC_PASSWD})
    vc_passwd_res = requests.post(url=url, data=vc_passwd_req, headers=headers)
    vc_passwd_list = vc_passwd_res.json()

    vc_info_list = list()
    for ip in vc_ip_list:
        info = dict()
        info[ip['param_name']] = ip['param_value_name']
        for user in vc_user_list:
            if ip['param_value_tag_name'] == user['param_value_tag_name']:
                info[user['param_name']] = user['param_value_name']
        for passwd in vc_passwd_list:
            if ip['param_value_tag_name'] == passwd['param_value_tag_name']:
                info[passwd['param_name']] = passwd['param_value_name']
        vc_info_list.append(info)
    return vc_info_list


def get_avaliable_ip(network, token):
    """
    调用ip池接口获取可用ip
    """
    path = "/ivmware/network/recommend-ip/"
    url = SERVER_ADDR + path
    headers = {'Content-Type': 'application/json', 'Authorization': token}
    data = json.dumps({"network": network})
    r = requests.post(url=url, data=data, headers=headers)
    data = r.json().get('data')
    return data['avaliable_ipaddr']
