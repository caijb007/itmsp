# coding: utf-8
# Author: ld

from . import serializers
from .models import *
from traceback import format_exc
from iuser.permissions import *
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .utils import *
from itmsp.utils.base import logger, smart_get
from itmsp.utils.decorators import post_data_to_dict
from django.db.models import Q
import copy
import interface_config
import requests


class BlueComponentDefinitionViewSet(ModelViewSet):
    """
    蓝图组件库操作
    """
    queryset = BlueComponentDefinition.objects.all()
    serializer_class = serializers.BlueComponentDefinitionSerializer

    @action(detail=False, methods=['get'], url_path='component-type')
    def component_type(self, request, *args, **kwargs):
        """
        获取组件实体类型
        """
        msg_prefix = u"获取组件实体类型 "
        try:
            component_type = COMPONENT_TYPE
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": component_type})

    @action(detail=False, methods=['post'], url_path='category-of-type')
    def category_of_type(self, request, *args, **kwargs):
        """
        获取组件实体分类
        """
        msg_prefix = u"获取组件实体分类 "
        req_dict = post_data_to_dict(request.data)
        component_type = smart_get(req_dict, 'component_type', int)
        try:
            component_category = set()
            queryset = self.get_queryset().filter(component_type=component_type)
            for cc in queryset:
                component_category.add(cc.component_category)

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": component_category})

    @action(detail=False, methods=['post'], url_path='component-of-category')
    def component_of_category(self, request, *args, **kwargs):
        """
        获取分类组件实体
        """
        msg_prefix = u"获取分类组件实体 "
        req_dict = post_data_to_dict(request.data)
        component_type = smart_get(req_dict, 'component_type', int)
        component_category = smart_get(req_dict, 'component_category', str)
        try:
            component_def_set = BlueComponentDefinition.objects.filter(component_type=component_type,
                                                                       component_category=component_category)

            component_Q = Q()

            component_Q.connector = 'OR'
            for component_def in component_def_set:
                component_Q.children.append(('id', component_def.component_entity))

            if component_type == 0:
                instance = BlueInterfaceDefinition.objects.filter(component_Q, is_freeze=False, is_component=True)
                serializer = serializers.BlueInterfaceDefinitionSerializer(instance=instance, many=True)
            elif component_type == 1:
                instance = BluePreParamGroup.objects.filter(component_Q, is_freeze=False, is_component=True)
                serializer = serializers.BluePreParamGroupSerializer(instance=instance, many=True)
            elif component_type == 2:
                instance = BlueAccessModuleParamGroup.objects.filter(component_Q, is_freeze=False, is_component=True)
                serializer = serializers.BlueAccessModuleParamGroupSerializer(instance=instance, many=True)
            elif component_type == 3:
                instance = BluePrintDefinition.objects.filter(component_Q, is_freeze=False, is_component=True)
                serializer = serializers.BluePrintDefinitionSerializer(instance=instance, many=True)
            else:
                raise Exception(u"不支持的组件类型， 请联系管理员！")
            # component_entity_set = BlueComponentEntityDefinition.objects.filter(component_Q, is_freeze=False)
            # serializer = serializers.BlueComponentEntityDefinitionSerializer(instance=component_entity_set, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})


class BlueComponentCategoryViewSet(ModelViewSet):
    """
    蓝图组件分组操作
    """
    queryset = BlueComponentCategory.objects.all()
    serializer_class = serializers.BlueComponentCategorySerializer


#
# class BlueComponentEntityDefinitionViewSet(ModelViewSet):
#     """
#     蓝图组件实体操作
#     """
#     queryset = BlueComponentEntityDefinition.objects.all()
#     serializer_class = serializers.BlueComponentEntityDefinitionSerializer


class BlueInterfaceCategoryViewSet(ModelViewSet):
    """
    接口分组
    """
    queryset = BlueInterfaceCategory.objects.all()
    serializer_class = serializers.BlueInterfaceCategorySerializer

    def destroy(self, request, *args, **kwargs):
        """
        """
        msg_prefix = u"删除接口分组 "
        try:
            instance = self.get_object()
            if instance.name == DEFAULT_CATEGORY:
                raise Exception(u"内置分组不能删除")
            else:
                # 删除分类后将分类下接口分组修改为 默认分组
                default_category, created = BlueInterfaceCategory.objects.get_or_create(name=DEFAULT_CATEGORY)
            interface_set = BlueInterfaceDefinition.objects.filter(category=instance)
            for interface in interface_set:
                interface.category = default_category
                interface.save()
            self.perform_destroy(instance)

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})


class BluePreParamGroupCategoryViewSet(ModelViewSet):
    """
    蓝图预定义参数组分组操作
    """
    queryset = BluePreParamGroupCategory.objects.all()
    serializer_class = serializers.BluePreParamGroupCategorySerializer


class BlueAccessModuleParamGroupCategoryViewSet(ModelViewSet):
    """
    蓝图接入模块参数组分组操作
    """
    queryset = BlueAccessModuleParamGroupCategory.objects.all()
    serializer_class = serializers.BlueAccessModuleParamGroupCategorySerializer


class BlueCategoryViewSet(ModelViewSet):
    """
    蓝图类别操作
    """
    queryset = BlueCategory.objects.all()
    serializer_class = serializers.BlueCategorySerializer

    def destroy(self, request, *args, **kwargs):
        """
        """
        msg_prefix = u"删除蓝图分组 "
        try:
            blue_category = self.get_object()
            if blue_category.name == DEFAULT_CATEGORY:
                raise Exception(u"内置分组不能删除")
            else:
                # 删除分类后将分类下蓝图分组修改为 默认分组
                default_category, created = BlueCategory.objects.get_or_create(name=DEFAULT_CATEGORY)
            blue_print_set = BluePrintDefinition.objects.filter(category=blue_category)
            for blue_print in blue_print_set:
                blue_print.category = default_category
                blue_print.save()
            self.perform_destroy(blue_category)

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})


class BlueInterfaceDefinitionViewSet(ModelViewSet):
    """
    接口操作
    """
    queryset = BlueInterfaceDefinition.objects.all()
    serializer_class = serializers.BlueInterfaceDefinitionSerializer

    @action(detail=False, methods=['post'], url_path='get-interface')
    def get_interface(self, request):
        """
        根据类别过滤接口
        """
        msg_prefix = u"接口查询 "
        req_dict = post_data_to_dict(request.data)
        interface_category_id = smart_get(req_dict, 'interface_category_id', int)
        try:
            is_freeze = request.data.get('is_freeze')
            if isinstance(is_freeze, bool):
                queryset = self.get_queryset().filter(category_id=interface_category_id, freeze=is_freeze)
            else:
                queryset = self.get_queryset().filter(category_id=interface_category_id)
            serializer = self.get_serializer(instance=queryset, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})

    @action(detail=False, url_path='update-url')
    def update_url(self, request):
        """
        - 生成接口配置文件中接口数据
        """
        msg_prefix = u"接口url查询 "
        try:
            urls = interface_config.blue_url
            for url in urls:
                requests.options(url)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": 1, "data": urls})

    # @action(detail=False, url_path='get-params-url')
    # def get_params_url(self, request):
    #     """
    #     - 获取参数列表所需url
    #     """
    #     msg_prefix = u"接口url查询 "
    #     try:
    #         param_urls = interface_config.params_url
    #
    #     except Exception, e:
    #         msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
    #         logger.error(format_exc())
    #         return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     else:
    #         msg = msg_prefix + u"成功!"
    #         return Response({"status": 1, "msg": 1, "data": param_urls})

    @action(detail=True, methods=['POST'], url_path='interface-params')
    def interface_params(self, request, *args, **kwargs):
        """
        获取接口参数
        """
        msg_prefix = u"获取接口参数 "
        req_dict = post_data_to_dict(request.data)
        io_stream = smart_get(req_dict, 'io_stream', str)
        try:
            interface_instance = self.get_object()
            params = interface_instance.params.filter(io_stream=io_stream)
            interface_params_serializer = serializers.BlueInterfaceParamSerializer(instance=params, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": interface_params_serializer.data})

    @action(detail=True, methods=['post'], url_path='interface-component')
    def interface_component(self, request, *args, **kwargs):
        """
        组件库添加/删除接口实体
        """
        msg_prefix = u"组件库添加/删除接口实体 "
        try:
            interface_instance = self.get_object()
            interface_category = interface_instance.category.name
            if interface_instance.is_component:
                blue_component_set = BlueComponentDefinition.objects.filter(component_entity=interface_instance.id)
                for blue_component in blue_component_set:
                    blue_component.delete()
            else:
                blue_component_serializer = serializers.BlueComponentDefinitionSerializer(data=dict(
                    component_category=interface_category,
                    component_type=0,
                    component_entity=interface_instance.id
                ))
                blue_component_serializer.is_valid()
                self.perform_create(blue_component_serializer)
            interface_instance.is_component = not interface_instance.is_component
            interface_instance.save()

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})


class BluePreParamGroupViewSet(ModelViewSet):
    """
    蓝图预定义参数组操作
    """
    queryset = BluePreParamGroup.objects.all()
    serializer_class = serializers.BluePreParamGroupSerializer

    @action(detail=True, methods=['post'], url_path='pre-group-params')
    def pre_group_params(self, request, *args, **kwargs):
        """
        获取预定义参数组参数
        """
        msg_prefix = u"获取预定义参数组参数 "
        try:
            pre_group_params_instance = self.get_object()
            params = pre_group_params_instance.params.all()
            pre_group_params_serializer = serializers.BluePreParamGroupParamSerializer(instance=params,
                                                                                       many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": pre_group_params_serializer.data})

    @action(detail=True, methods=['post'], url_path='pre-param-group-component')
    def pre_param_group_component(self, request, *args, **kwargs):
        msg_prefix = u"组件库添加/删除预定义参数组实体 "
        try:
            pre_param_group_instance = self.get_object()
            pre_param_group_category = pre_param_group_instance.category.name

            if pre_param_group_instance.is_component:
                blue_component_set = BlueComponentDefinition.objects.filter(
                    component_entity=pre_param_group_instance.id)
                for blue_component in blue_component_set:
                    blue_component.delete()
            else:
                blue_component_serializer = serializers.BlueComponentDefinitionSerializer(data=dict(
                    component_category=pre_param_group_category,
                    component_type=1,
                    component_entity=pre_param_group_instance.id
                ))
                blue_component_serializer.is_valid()
                self.perform_create(blue_component_serializer)
            pre_param_group_instance.is_component = not pre_param_group_instance.is_component
            pre_param_group_instance.save()
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})

    @action(detail=False, methods=['post'], url_path='get-pre-param-group')
    def get_pre_param_group(self, request):
        """
        根据类别过滤预定义参数组
        """
        msg_prefix = u"接口查询 "
        req_dict = post_data_to_dict(request.data)
        pre_param_group_id = smart_get(req_dict, 'pre_param_group_id', int)
        try:
            # is_freeze 测试不通过 is_freeze类型未符合要求
            is_freeze = request.data.get('is_freeze')
            if isinstance(is_freeze, bool):
                queryset = self.get_queryset().filter(category_id=pre_param_group_id, is_freeze=is_freeze)
            else:
                queryset = self.get_queryset().filter(category_id=pre_param_group_id)
            serializer = self.get_serializer(instance=queryset, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})


class BlueAccessModuleParamGroupViewSet(ModelViewSet):
    """
    蓝图接入模块参数组操作
    """
    queryset = BlueAccessModuleParamGroup.objects.all()
    serializer_class = serializers.BlueAccessModuleParamGroupSerializer

    @action(detail=True, methods=['post'], url_path='acc-module-component')
    def acc_module_component(self, request, *args, **kwargs):
        msg_prefix = u"组件库添加/删除接入模块参数组实体 "
        try:
            acc_module_instance = self.get_object()
            acc_module_category = acc_module_instance.category.name

            if acc_module_instance.is_component:
                blue_component_set = BlueComponentDefinition.objects.filter(
                    component_entity=acc_module_instance.id)
                for blue_component in blue_component_set:
                    blue_component.delete()
            else:
                blue_component_serializer = serializers.BlueComponentDefinitionSerializer(data=dict(
                    component_category=acc_module_category,
                    component_type=2,
                    component_entity=acc_module_instance.id
                ))
                blue_component_serializer.is_valid()
                self.perform_create(blue_component_serializer)
            acc_module_instance.is_component = not acc_module_instance.is_component
            acc_module_instance.save()
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})

    @action(detail=True, methods=['post'], url_path='acc-module-params')
    def acc_module_params(self, request, *args, **kwargs):
        """
        蓝图接入模块参数组参数
        """
        msg_prefix = u"蓝图接入模块参数组参数 "
        try:
            acc_module_params_instance = self.get_object()
            params = acc_module_params_instance.params.all()
            pre_group_params_serializer = serializers.BlueAccessModuleParamsGroupParamSerializer(instance=params,
                                                                                                 many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": pre_group_params_serializer.data})

    @action(detail=False, methods=['post'], url_path='get-acc-module-param-group')
    def get_acc_module_param_group(self, request):
        """
        根据类别过滤接入模块参数组
        """
        msg_prefix = u"接口查询 "
        req_dict = post_data_to_dict(request.data)
        acc_module_param_group_id = smart_get(req_dict, 'acc_module_param_group_id', int)
        try:
            # is_freeze 测试不通过 is_freeze类型未符合要求
            is_freeze = request.data.get('is_freeze')
            if isinstance(is_freeze, bool):
                queryset = self.get_queryset().filter(category_id=acc_module_param_group_id, is_freeze=is_freeze)
            else:
                queryset = self.get_queryset().filter(category_id=acc_module_param_group_id)
            serializer = self.get_serializer(instance=queryset, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})


class BlueInterfaceParamViewSet(ModelViewSet):
    """
    接口参数
    """
    queryset = BlueInterfaceParam.objects.all()
    serializer_class = serializers.BlueInterfaceParamSerializer


class BluePreParamGroupParamViewSet(ModelViewSet):
    """
    蓝图预定义参数组参数操作
    """
    queryset = BluePreParamGroupParam.objects.all()
    serializer_class = serializers.BluePreParamGroupParamSerializer


class BlueAccessModuleParamsGroupParamViewSet(ModelViewSet):
    """
    蓝图接入模块参数组参数操作
    """
    queryset = BlueAccessModuleParamsGroupParam.objects.all()
    serializer_class = serializers.BlueAccessModuleParamsGroupParamSerializer


class BluePrintDefinitionViewSet(ModelViewSet):
    """
    蓝图操作
    """
    queryset = BluePrintDefinition.objects.all()
    serializer_class = serializers.BluePrintDefinitionSerializer

    # @action(detail=False, methods=['post'], url_path='delete-all-blue')
    # def delete_all_blue(self, request):
    #     msg_prefix = "删除蓝图 "
    #     try:
    #         blue = BluePrintDefinition.objects.filter(created_user_id=1).delete()
    #     except Exception, e:
    #         msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
    #         logger.error(format_exc())
    #         return Response({"status": -1, "msg": msg, "data": {}},
    #                         status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     else:
    #         msg = msg_prefix + u"成功!"
    #         return Response({"status": 1, "msg": msg, "data": len(blue)})

    def list(self, request, *args, **kwargs):
        msg_prefix = "获取蓝图列表 "
        try:
            query_set = self.get_queryset().filter(keep_status=1)
            serializer = self.get_serializer(instance=query_set, many=True)

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})

    def create(self, request, *args, **kwargs):
        msg_prefix = "创建/获取蓝图草稿 "
        req_dict = post_data_to_dict(request.data)
        category, created = BlueCategory.objects.get_or_create(name=DEFAULT_CATEGORY)
        try:
            blue_instance = BluePrintDefinition.objects.filter(created_user=request.user, keep_status=0).last()
            if blue_instance:
                serializer = self.get_serializer(blue_instance)
            else:
                req_dict['created_user'] = request.user.name
                req_dict['category'] = category
                serializer = self.get_serializer(data=req_dict)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})

    @action(detail=True, methods=['post'], url_path='recurring-blue')
    def recurring_blue(self, request, *args, **kwargs):
        msg_prefix = "复现蓝图 "
        try:
            old_blue_print = self.get_object()
            # 清空当前用户草稿
            BluePrintDefinition.objects.filter(created_user=request.user, keep_status=0).delete()

            # 生成新蓝图草稿
            new_blue_print = copy.deepcopy(old_blue_print)
            new_blue_print.id = None
            new_blue_print.pk = None
            # new_blue_print.tmp = old_blue_print.id  # 缓存功能为使用
            new_blue_print.avaliable_node_sort = None
            new_blue_print.keep_status = 0
            new_blue_print.created_user = request.user
            new_blue_print.is_component = 0
            new_blue_print.is_valid = 0
            new_blue_print.is_verify = 0
            new_blue_print.save()

            # 新旧节点对应字典
            correspond = dict()

            # 生成新节点并对应新旧节点id
            for old_node in old_blue_print.blue_nodes.all():
                new_node = copy.deepcopy(old_node)
                new_node.id = None
                new_node.save()
                new_blue_print.blue_nodes.add(new_node)
                correspond[old_node.id] = new_node.id

            # 新节点生成吓一跳
            for old_node in old_blue_print.blue_nodes.all():
                new_node = new_blue_print.blue_nodes.get(id=correspond[old_node.id])
                downstream_nodes = old_node.downstream_node.all()
                for down_node in downstream_nodes:
                    new_node.downstream_node.add(correspond[down_node.id])

            # 更改节点映射表对应关系
            blue_node_map_set = BlueNodeMapParam.objects.filter(blue_print=old_blue_print.id)
            for blue_node_map in blue_node_map_set:
                new_blue_node_map = copy.deepcopy(blue_node_map)
                new_blue_node_map.id = None
                new_blue_node_map.blue_print_id = new_blue_print.id
                new_blue_node_map.target_node = correspond[new_blue_node_map.target_node]
                new_blue_node_map.source_node = correspond[new_blue_node_map.source_node]
                new_blue_node_map.save()
            # new_blue_print.save()
            new_nodes = new_blue_print.blue_nodes.filter(component_type=0)
            if not len(new_nodes):
                raise Exception(u"无节点")
            is_valid_params(new_nodes)
            graph = build_graph(new_nodes)
            avaliable_node_sort = topo_sort(graph)
            if not avaliable_node_sort:
                raise Exception(u"节点存在环， 请检查")
            new_blue_print.avaliable_node_sort = avaliable_node_sort
            new_blue_print.is_verify = True
            for node in new_nodes:
                if not node.is_verify:
                    new_blue_print.is_verify = False
                    raise Exception(u"请先验证蓝图节点")

            # 更新画板数据
            link_data = new_blue_print.link_data[0]
            # 节点坐标
            nodes_locs = link_data['nodes_loc']
            # 节点关系
            links = link_data['link']
            for loc in nodes_locs:
                loc['id'] = correspond[loc['id']]

            for link in links:
                link['from'] = correspond[link['from']]
                link['to'] = correspond[link['to']]
            new_blue_print.save()

            serializer = self.get_serializer(instance=new_blue_print)

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})

    @action(detail=True, methods=['post'], url_path='blue-print-component')
    def blue_print_component(self, request, *args, **kwargs):
        """
        组件库添加/删除蓝图
        """
        msg_prefix = u"组件库添加/删除蓝图 "
        try:
            blue_print_instance = self.get_object()
            blue_print_category = blue_print_instance.category.name

            if blue_print_instance.is_component:
                blue_component_set = BlueComponentDefinition.objects.filter(component_entity=blue_print_instance.id)
                for blue_component in blue_component_set:
                    blue_component.delete()
            else:
                blue_component_serializer = serializers.BlueComponentDefinitionSerializer(data=dict(
                    component_category=blue_print_category,
                    component_type=0,
                    component_entity=blue_print_instance.id
                ))
                blue_component_serializer.is_valid()
                self.perform_create(blue_component_serializer)
            blue_print_instance.is_component = not blue_print_instance.is_component
            blue_print_instance.save()

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})

    @action(detail=False, methods=['post'])
    def get_blue(self, request):
        """
        根据类别过滤蓝图
        * 参数
        ** category_name, 分类名， str
        """
        msg_prefix = u"蓝图过滤 "
        try:
            blue_category_id = request.data.get('blue_category_id')
            queryset = self.get_queryset().filter(category_id=blue_category_id, keep_status=1)
            serializer = self.get_serializer(instance=queryset, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})

    @action(detail=True, methods=['get'], url_path='get-blue-node')
    def get_blue_nodes(self, request, *args, **kwargs):
        """
        获取蓝图节点
        """
        msg_prefix = u"获取蓝图节点 "
        try:
            blue_print_instance = self.get_object()
            nodes = blue_print_instance.blue_nodes.all()
            nodes_serializer = serializers.BlueNodeDefinitionSerializer(instance=nodes, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": nodes_serializer.data})

    @action(detail=True, methods=['post'], url_path='link-data')
    def link_data(self, request, *args, **kwargs):
        """
        画板连线数据
        * 参数
        ** link_data， 连线数据, list
        """
        msg_prefix = u"更新画板连线数据 "
        req_dict = post_data_to_dict(request.data)
        link_data = smart_get(req_dict, 'link_data', list)
        try:
            blue_print = self.get_object()
            blue_print.link_data = link_data
            blue_print.save()
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})

    @action(detail=True, methods=['get'], url_path='check-blue')
    def check_blue(self, request, *args, **kwargs):
        """
        检查蓝图节点
        """
        msg_prefix = u"检查蓝图节点 "
        try:
            blue_print_instance = self.get_object()
            nodes = blue_print_instance.blue_nodes.filter(component_type=0)
            if not len(nodes):
                raise Exception(u"蓝图没有节点")
            is_valid_params(nodes)  # 检查参数
            graph = build_graph(nodes)  # 构建图
            avaliable_node_sort = topo_sort(graph)  # 图排序
            if not avaliable_node_sort:
                raise Exception(u"节点存在环， 请检查")
        except Exception, e:
            msg = unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}})
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})

    @action(detail=True, methods=['post'], url_path='save-blue')
    def save_blue(self, request, *args, **kwargs):
        """
        验证节点参数, 排序, 保存蓝图
        """
        msg_prefix = u"保存蓝图 "
        req_dict = post_data_to_dict(request.data)
        blue_category_id = smart_get(req_dict, 'blue_category_id', int)
        name = smart_get(req_dict, 'name', str)
        description = smart_get(req_dict, 'description', str)
        try:
            blue_print = self.get_object()
            if blue_category_id:
                blue_print.blue_category_id = blue_category_id
            blue_print.name = name
            blue_print.description = description

            nodes = blue_print.blue_nodes.filter(component_type=0)
            if not len(nodes):
                raise Exception(u"无节点")
            is_valid_params(nodes)  # 参数检查
            graph = build_graph(nodes)  # 构建图
            avaliable_node_sort = topo_sort(graph)  # 图排序
            if not avaliable_node_sort:
                raise Exception(u"节点存在环， 请检查")
            blue_print.avaliable_node_sort = avaliable_node_sort
            blue_print.is_verify = True
            for node in nodes:
                if not node.is_verify:
                    blue_print.is_verify = False
                    raise Exception(u"请先验证蓝图节点")
            blue_print_set = BluePrintDefinition.objects.filter(name=name)
            if len(blue_print_set):
                raise Exception(u"蓝图有重名， 请重新命名")
            blue_print.keep_status = 1
            blue_print.save()
        except Exception, e:
            msg = unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}})
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})


class BlueNodeDefinitionViewSet(ModelViewSet):
    """
    蓝图节点操作
    """
    queryset = BlueNodeDefinition.objects.all()
    serializer_class = serializers.BlueNodeDefinitionSerializer

    def create(self, request, *args, **kwargs):
        """
        创建节点
        """
        msg_prefix = u"创建节点 "
        req_dict = post_data_to_dict(request.data)
        component_id = smart_get(req_dict, 'component_id', int)
        component_type = smart_get(req_dict, 'component_type', int)
        blue_print_id = smart_get(req_dict, 'blue_print_id', int)
        try:
            commonent_instance_params = None
            if component_type == 0:  # 接口
                instance_set = BlueInterfaceDefinition.objects.filter(id=component_id)
                for instance in instance_set:
                    commonent_instance_params = serializers.BlueInterfaceParamSerializer(
                        instance.params.all(), many=True).data
                serializer = serializers.BlueInterfaceDefinitionSerializer(instance=instance_set, many=True).data[0]
            elif component_type == 1:  # 参数
                instance_set = BluePreParamGroup.objects.filter(id=component_id)
                for instance in instance_set:
                    commonent_instance_params = serializers.BluePreParamGroupParamSerializer(
                        instance.params.all(), many=True).data
                serializer = serializers.BluePreParamGroupSerializer(instance=instance_set, many=True).data[0]
            elif component_type == 2:  # 模块
                instance_set = BlueAccessModuleParamGroup.objects.filter(id=component_id)
                for instance in instance_set:
                    commonent_instance_params = serializers.BlueAccessModuleParamsGroupParamSerializer(
                        instance.params.all(), many=True).data
                serializer = serializers.BlueAccessModuleParamGroupSerializer(instance=instance_set, many=True).data[0]
            elif component_type == 3:  # 蓝图
                instance_set = BluePrintDefinition.objects.filter(id=component_id)
                serializer = serializers.BluePrintDefinitionSerializer(instance=instance_set, many=True).data[0]
            else:
                instance_set = list()
                serializer = list()
                commonent_instance_params = list()

            if not len(instance_set):
                raise Exception(u"组件不存在， 请联系管理员！")

            serializer.update(params=commonent_instance_params)
            kwargs = dict(
                name=instance_set[0].name,
                blue_print=blue_print_id,
                component_type=component_type,
                component_data=serializer
            )

            blue_node_serializer = self.get_serializer(data=kwargs)
            blue_node_serializer.is_valid(raise_exception=True)
            blue_node_instance = blue_node_serializer.save()
            blue_node_instance.key = blue_node_instance.id
            blue_node_instance.save()
            blue_print_instance = BluePrintDefinition.objects.get(id=blue_print_id)
            blue_print_instance.keep_status = 0
            blue_print_instance.save()
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            response = Response({"status": 1, "msg": msg, "data": blue_node_serializer.data})
            return response

    @action(detail=False, methods=['post'], url_path='node-params')
    def node_params(self, request, *args, **kwargs):
        """
        获取节点参数及参数映射信息
        * 参数
        ** source_id， 来源节点id, int
        ** target_id, 目标节点id, int
        """
        msg_prefix = u"获取节点参数及参数映射信息 "
        req_dict = post_data_to_dict(request.data)
        source_id = smart_get(req_dict, 'source_id', int)
        target_id = smart_get(req_dict, 'target_id', int)
        try:
            source_node_instance = self.get_queryset().get(id=source_id)
            target_node_instance = self.get_queryset().get(id=target_id)

            target_params = target_node_instance.component_data.get('params')
            source_params = source_node_instance.component_data.get('params')

            # 两个节点间映射集合
            exist_map_self_set = BlueNodeMapParam.objects.filter(target_node=target_id, source_node=source_id)
            # 目标节点所有映射集合
            exist_map_all_set = BlueNodeMapParam.objects.filter(target_node=target_id)

            exist_params = serializers.BlueNodeMapParamSerializer(instance=exist_map_self_set, many=True).data

            # 参数过滤
            for target_param in copy.deepcopy(target_params):
                # 删除输出项
                have_io_stream = "io_stream" in [k for k, _ in target_param.items()]
                if have_io_stream:
                    if target_param['io_stream'] == "输出":
                        target_params.remove(target_param)
                        continue
                # 删除其它节点已映射项
                for exist_map in exist_map_all_set:
                    if exist_map.target_param_name == target_param['param_name'] and exist_map.source_node != source_id:
                        target_params.remove(target_param)
                        continue

                for source_param in copy.deepcopy(source_params):
                    # 删除输入项
                    have_io_stream = "io_stream" in [k for k, _ in source_param.items()]
                    if have_io_stream:
                        if source_param['io_stream'] == "输入":
                            source_params.remove(source_param)
                            continue

            params = dict(
                source_params=source_params,
                target_params=target_params,
                exist_params=exist_params
            )
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": params})

    @action(detail=False, methods=['post'], url_path='related-node')
    def related_node(self, request, *args, **kwargs):
        """
        节点间关系(上下游)
        * 参数
        ** up_id, 上游节点id, int
        ** down_id, 下游节点id, int
        ** is_related, 是否添加关系, bool
        """
        msg_prefix = u"更新节点间关系 "
        req_dict = post_data_to_dict(request.data)
        up_id = smart_get(req_dict, 'up_id', int)
        down_id = smart_get(req_dict, 'down_id', int)
        is_related = smart_get(req_dict, 'is_related', bool, False)
        try:
            up_instance = BlueNodeDefinition.objects.get(id=up_id)
            if is_related:
                up_instance.downstream_node.add(down_id)
            else:
                up_instance.downstream_node.remove(down_id)
                node_map_set = BlueNodeMapParam.objects.filter(target_node=down_id, source_node=up_id)
                for node_map in node_map_set:
                    node_map.delete()
            up_instance.save()
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})

    def destroy(self, request, *args, **kwargs):
        """
        删除节点
        """
        msg_prefix = u"删除节点 "
        try:
            node_instance = self.get_object()

            # 删除节点关联映射表
            component_Q = Q()
            component_Q.connector = 'OR'
            component_Q.children.append(('target_node', node_instance.id))
            component_Q.children.append(('source_node', node_instance.id))
            node_map_set = BlueNodeMapParam.objects.filter(component_Q)
            for node_map in node_map_set:
                node_map.delete()
            # 删除节点
            self.perform_destroy(node_instance)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})


class BlueNodeMapParamViewSet(ModelViewSet):
    """
    蓝图节点-参数操作
    create
    创建节点-参数映射关系
    * 参数
    ** map_list, 映射关系列表, list
    ** source_id, 来源节点, int
    ** target_id, 目标节点, int
    """
    queryset = BlueNodeMapParam.objects.all()
    serializer_class = serializers.BlueNodeMapParamSerializer

    def create(self, request, *args, **kwargs):
        msg_prefix = u"创建节点-参数映射关系 "
        req_dict = post_data_to_dict(request.data)

        map_list = smart_get(req_dict, 'map_list', list)
        source_id = smart_get(req_dict, 'source_id', int)
        target_id = smart_get(req_dict, 'target_id', int)
        try:
            exist_map_set = self.get_queryset().filter(source_node=source_id, target_node=target_id)
            for exist_map in exist_map_set:
                exist_map.delete()

            for map in map_list:
                serializer = self.get_serializer(data=map)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": {}})


class BlueInstanceViewSet(ModelViewSet):
    """
    蓝图实例操作
    """
    queryset = BlueInstance.objects.all()
    serializer_class = serializers.BlueInstanceSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='order-list')
    def order_list(self, request, *args, **kwargs):
        """
        给列表排序

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"筛选"
        # req_dict = post_data_to_dict(request.data)
        status_num = request.data.get("status")
        order_reverse = request.data.get("order_reverse")
        # order_queryset = self.get_queryset().filter(status=status_num)
        # # status_num = smart_get(req_dict, "status", str)
        # # order_reverse = smart_get(req_dict, "order_reverse", str)
        #
        # ori_queryset = self.get_queryset()
        # ori_queryset_ord = self.get_queryset().order_by("-" + "id")
        #
        # order_queryset_reverse = self.get_queryset().filter(status=status_num).order_by("-" + "startTime")
        # if not (status_num and order_reverse):
        #     serializer = self.get_serializer(instance=ori_queryset, many=True)
        # elif status_num == '' and order_reverse == '-':
        #     serializer = self.get_serializer(instance=ori_queryset_ord, many=True)
        #
        # if order_reverse == "-":
        #     serializer = self.get_serializer(instance=order_queryset_reverse, many=True)
        # else:
        #     serializer = self.get_serializer(instance=order_queryset, many=True)
        # # serializer = self.get_serializer(instance=order_queryset, many=True)
        try:

            if not order_reverse and status_num:  # 進行中 默認
                order_queryset = self.get_queryset().filter(status=status_num)
                serializer = self.get_serializer(instance=order_queryset, many=True)
                # ori_queryset = self.get_queryset()
                # serializer = self.get_serializer(instance=ori_queryset, many=True)
            elif not status_num and order_reverse:  # 默認 倒敘
                ori_queryset_ord = self.get_queryset().order_by("-" + "id")
                serializer = self.get_serializer(instance=ori_queryset_ord, many=True)
            elif status_num and order_reverse:
                order_queryset_reverse = self.get_queryset().filter(status=status_num).order_by("-" + "startTime")
                serializer = self.get_serializer(instance=order_queryset_reverse, many=True)
            else:
                ori_queryset = self.get_queryset()
                serializer = self.get_serializer(instance=ori_queryset, many=True)

        except Exception, e:
            msg = msg_prefix + u"失败，错误信息:" + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})
            # return Response({"status": 1, "msg": msg, "data": []})


class NodeInstanceViewSet(ModelViewSet):
    """
    节点实例操作
    """
    queryset = NodeInstance.objects.all()
    serializer_class = serializers.NodeInstanceSerializer


class BlueAccessModuleParamsInstanceViewSet(ModelViewSet):
    """

    """
    queryset = BlueAccessModuleParamsInstance.objects.all()
    serializer_class = serializers.BlueAccessModuleParamsInstanceSerializer


class BlueEngineTaskViewSet(ModelViewSet):
    """

    """
    queryset = BlueEngineTask.objects.all()
    serializer_class = serializers.BlueEngineTaskSerializer
