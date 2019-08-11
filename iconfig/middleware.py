# coding: utf-8
# Author: ld
"""
监听option请求
作用：将接口配置文件中记录的接口文档写入数据库，包括接口name、描述、输入/输出参数
"""

from itmsp.settings import LOCAL_HOST, LOCAL_PORT
from .models import *
import re

URL_PREFIX = "http://" + LOCAL_HOST + ":" + LOCAL_PORT


class InterfaceMiddleware(object):
    """
    接口添加到数据库(需按模块接口文档注释格式书写注释, 书写格式参照模块文件readme.md)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        response = self.get_response(request)
        self.options_method(request, response)
        return response

    def options_method(self, request, response):
        """
        监听options请求，并获取文档注释
        """
        if request.method == 'OPTIONS':
            description = response.data.get('description').encode()
            if description:
                func_name = response.data.get('name').encode()
                data = re.split(r'[\n]', description)
                if data:
                    descriptions = list()
                    for desc in data:
                        line = re.sub(r'[\s\n]', '', desc)  # 去除空白字符
                        if len(line):
                            descriptions.append(line)
                    self.handle_data(descriptions, func_name, request)

    def handle_data(self, descriptions, func_name, request):
        """
        处理文档数据
        """
        stars = re.compile(r'\*')
        bars = re.compile(r'[\-]')
        addr = re.compile(r'&')

        inputs = []
        outputs = []
        requires = []
        description = None
        name = None
        for desc in descriptions:
            num_star = stars.findall(desc)  # 获取每一行存在'*'的列表
            num_bar = bars.findall(desc)  # 获取每一行存在'-'的列表
            num_addr = addr.findall(desc)  # 获取每一行存在'&'的列表
            if len(num_bar) == 1:
                description = desc[1:]
            elif len(num_bar) == 2:
                requires = desc[2:].split(":")[1:]
            elif len(num_star) == 2:
                inputs.append(desc[2:])
            elif len(num_star) == 3:
                outputs.append(desc[3:])
            elif len(num_addr) == 1:
                name = desc[1:]

        requires = requires[0].split(',')

        interface = self.handle_interface(description, name, func_name, request)
        self.handle_params(interface, inputs, outputs, requires)

    def handle_interface(self, description, name, func_name, request):
        """
        处理接口基本数据， 写入接口数据库
        """
        url = URL_PREFIX + request.path
        interface_set = BlueInterfaceDefinition.objects.filter(url=url)
        # 修改接口数据
        if interface_set.exists():
            interface = interface_set[0]
            if not interface.description or interface.description != description:
                interface.description = description
            if not interface.func_name or interface.func_name != func_name:
                interface.func_name = func_name
            if not interface.name or interface.name != name:
                interface.name = name
            interface.save()
        else:
            # 新建接口数据
            category, created = BlueInterfaceCategory.objects.get_or_create(name=DEFAULT_CATEGORY)
            interface = BlueInterfaceDefinition.objects.create(url=url, description=description,
                                                               func_name=func_name, category=category, name=name)
        return interface

    def handle_params(self, interface, inputs, outputs, requires):
        """
        处理接口输入、输出参数, 并写入参数数据库
        """
        params_set = interface.params.all()

        # 参数表去除取消的参数
        for param in params_set:
            if param.param_name not in (inputs):
                param.delete()

        for input in inputs:
            input_list = input.split(',')
            param_name_in = input_list[0]
            description_in = input_list[1]
            data_type_in = input_list[2]

            param_set_in = params_set.filter(param_name=param_name_in)
            if len(param_set_in):
                param_in = param_set_in[0]
                param_in.interface = interface
                param_in.require = param_name_in in requires
                param_in.data_type = data_type_in
                param_in.io_stream = 'input'
                param_in.description = description_in
                param_in.save()
            else:
                BlueInterfaceParam.objects.create(
                    blue_interface=interface,
                    param_name=param_name_in,
                    require=param_name_in in requires,
                    data_type=data_type_in,
                    io_stream='input',
                    description=description_in
                )

        for output in outputs:
            output_list = output.split(',')
            param_name_out = output_list[0]
            description_out = output_list[1]
            data_type_out = output_list[2]

            param_set_out = params_set.filter(param_name=param_name_out)
            if len(param_set_out):
                param_out = param_set_out[0]
                param_out.interface = interface
                param_out.data_type = data_type_out
                param_out.io_stream = 'output'
                param_out.description = description_out
                param_out.save()
            else:
                BlueInterfaceParam.objects.create(
                    blue_interface=interface,
                    param_name=param_name_out,
                    io_stream='output',
                    data_type=data_type_out,
                    description=description_out
                )
        return
