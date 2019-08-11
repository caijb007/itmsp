# coding: utf-8
# Author: Dunkle Qiu

import struct
import logging
import subprocess
import socket
import os
import StringIO
import re
from itmsp.models import DataDict
from xlsxwriter import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range
from itmsp.settings import *
from django.http import QueryDict, StreamingHttpResponse
from rest_framework.parsers import DataAndFiles
from Crypto import Util
from traceback import format_exc


# 定义全局常量
class ROLES(object):
    """用户角色"""
    SU = ('SU', 'SuperUser')
    GM = ('GM', 'GroupManager')
    CU = ('CU', 'CommonUser')
    SN = ('SN', 'ServiceNode')

    @classmethod
    def as_choice(cls):
        return cls.SU, cls.GM, cls.CU, cls.SN,


class OSTYPES(object):
    """操作系统类型"""
    WIN = ('Windows', 'Windows OS')
    LNX = ('Linux', 'Linux OS')

    @classmethod
    def as_choice(cls):
        return cls.WIN, cls.LNX,


# 基础处理函数
def split(str_li, sep=','):
    if not (isinstance(sep, str) and len(sep) == 1):
        raise TypeError("Sep should be a simple char such as ','")
    if not str_li:
        return []
    return str_li.split(sep)


def is_true(var):
    if isinstance(var, unicode):
        var = str(var)
    if isinstance(var, str):
        return var.lower() not in ('false', 'no', '0', 'n', '')
    else:
        return bool(var)


def smart_get(dic, key, cls, default=None, **kwargs):
    """
    从request post dict中取值并转化为期望的类型
    @param dic: 提取的字典
    @param key: 变量名
    @param cls: 取值的类型
    @param default: 取不到值时的默认值
    @param kwargs: 其他参数
    @return: 相应类型的返回值
    """
    assert isinstance(dic, dict)
    result = dic.get(key)
    if isinstance(result, cls):
        return result
    if cls is bool:
        return is_true(dic.get(key, default))
    elif cls is list:
        if dic.has_key(key):
            value = dic.get(key)
            if isinstance(value, (str, unicode)):
                return split(dic.get(key), kwargs.get('sep', ','))
            else:
                return [value]
        else:
            return kwargs.get('default_list', [])
    else:
        try:
            return default if result is None else cls(result)
        except:
            return default


def ip_bin2str(i_bin):
    if len(i_bin) < 32:
        i_bin = i_bin.rjust(32, str(0))
    i_raw = [i_bin[i * 8:(i + 1) * 8] for i in range(4)]
    i_str = [str(int(subn, 2)) for subn in i_raw]
    return '.'.join(i_str)


def ip_str2bin(i_str):
    i_raw = [bin(int(subn)) for subn in i_str.split('.')]
    if len(i_raw) != 4:
        return '0' * 32
    i_bin = [subn[2:].rjust(8, str(0)) for subn in i_raw]
    return ''.join(i_bin)


def ping(host, count=1, wait=1, port=None):
    args = ['ping', '-c', str(count), '-w', str(wait), host]
    status = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    ).wait()
    if status != 0:
        return False
    if not isinstance(port, int):
        return True
    # port不为空, 检测远程端口
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(1)
    try:
        sk.connect((host, port))
        return True
    except:
        return False


class REMatch(object):
    PT_date = "[0-9]{4}\-[01][0-9]\-[0-3][0-9]"

    def __init__(self, pt):
        self.pt = pt
        self.pattern = re.compile(pt)

    def match(self, match_string):
        """
        正则匹配
        @param match_string: 待匹配的文本
        @return: 匹配到的字符串列表
        """
        if not match_string:
            match_string = ""
        return self.pattern.findall(match_string)

    def can_match(self, match_string):
        return bool(self.match(match_string))

    def match_first(self, match_string):
        li = self.match(match_string)
        if li:
            return li[0]
        else:
            return None


def set_log(level, filename='itmsp.log', logger_name='itmsp'):
    """
    根据提示设置log打印
    """
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_file = os.path.join(LOG_DIR, filename)
    if not os.path.isfile(log_file):
        os.mknod(log_file)
        os.chmod(log_file, 0644)
    log_level_total = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARN, 'error': logging.ERROR,
                       'critical': logging.CRITICAL}
    logger_f = logging.getLogger(logger_name)
    logger_f.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    fh.setLevel(log_level_total.get(level, logging.DEBUG))
    formatter = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger_f.addHandler(fh)
    return logger_f


logger = set_log(LOG_LEVEL)


def bash(cmd):
    """
    执行bash命令
    """
    return subprocess.call(cmd, shell=True)


# 请求处理
def post_data_to_dict(data):
    """
    将request.data类型统一为dict
    """
    if isinstance(data, QueryDict):
        return data.dict()
    elif isinstance(data, DataAndFiles):
        return data.data.dict()
    elif isinstance(data, dict):
        return data
    else:
        raise Exception(u"POST传入参数须为json格式")


# 响应封装
def field_display(value, flt):
    if flt == "list":
        if not isinstance(value, list):
            raise TypeError
        return "\n".join(value)
    elif flt == "date":
        if not value:
            return ""
        return value.split("T")[0]
    elif flt == "datetime":
        if not value:
            return ""
        return value.replace("T", " ").split(".")[0]
    elif flt == "env_type":
        try:
            return DataDict.options.get(app='ovm', name='env_type', value=value).display
        except:
            return value


def write_xlsx(serializer, headers, title_text):
    output = StringIO.StringIO()
    workbook = Workbook(output)
    worksheet_s = workbook.add_worksheet('Summary')

    # Here we will adding the code to add data
    title = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })
    header = workbook.add_format({
        'bg_color': '#92d050',
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1
    })
    cell = workbook.add_format({
        'align': 'left',
        'valign': 'top',
        'text_wrap': False,
        'border': 1
    })
    hearder_len = len(headers)
    header_range = xl_range(0, 0, 0, hearder_len - 1)
    worksheet_s.merge_range(header_range, title_text, title)

    # column header
    for col, field in enumerate(headers):
        worksheet_s.write(1, col, field[1], header)
        worksheet_s.set_column(col, col, width=field[2])
    # column content
    for row, line in enumerate(serializer.data, start=2):
        # Write a line for each record
        for col, field in enumerate(headers):
            keys = field[0].split('.')
            value = line
            for key in keys[:-1]:
                value = value[key]
            if "|" in keys[-1]:
                key, flt = keys[-1].split("|")
                value = field_display(value[key], flt)
            else:
                value = value[keys[-1]]
            worksheet_s.write(row, col, value, cell)

    workbook.close()
    xlsx_data = output.getvalue()
    # xlsx_data contains the Excel file
    return xlsx_data


def stream_response(content, filename):
    response = StreamingHttpResponse(content_type='application/octet-stream')
    response['Content-Disposition'] = "attachment; filename={filename}".format(filename=filename)
    response.streaming_content = content
    return response


# chevah source
def NS(t):
    """
    net string
    """
    return struct.pack('!L', len(t)) + t


def MP(number):
    if number == 0:
        return b'\000' * 4
    assert number > 0
    bn = Util.number.long_to_bytes(number)
    if ord(bn[0]) & 128:
        bn = b'\000' + bn
    return struct.pack('>L', len(bn)) + bn


# 字节bytes转化kb\m\g
def formatSizetoKb(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
        return "Error"

    return "%f" % (kb)


# 获取文件大小
def getDocSize(path):
    try:
        size = os.path.getsize(path)
        return formatSizetoKb(size)
    except Exception as err:
        print(err)


# 获取文件夹大小
def getFileSize(path):
    sumsize = 0
    try:
        filename = os.walk(path)
        for root, dirs, files in filename:
            for fle in files:
                size = os.path.getsize(path + fle)
                sumsize += size
        return formatSizetoKb(sumsize)
    except Exception as err:
        print(err)


def zip(file):
    try:
        if os.path.exists(file):
            kb = getDocSize(file)
            fm = 5120
            fm = "%f" % (fm)
            if float(kb) > float(fm):
                file_name = os.path.basename(file)
                file_path = os.path.dirname(file)
                filename, ext = os.path.splitext(file_name)
                absolute_filename, absolute_ext = os.path.splitext(file)
                bash("cd " + file_path + ";zip " + filename + '.zip ' + file_name)
                zip_file = absolute_filename + ".zip"
                return zip_file
            return file
        else:
            return False
    except Exception as err:
        print format_exc()


def all_in(list_out, list_in):
    flag = True
    for list_out_item in list_out:
        if list_out_item not in list_in:
            flag = False
    return flag
