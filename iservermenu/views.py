# -*- coding: utf-8 -*-
# Author: Chery-Huo
from __future__ import unicode_literals

from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import *
from traceback import format_exc
from itmsp.utils.base import logger, smart_get
from itmsp.utils.decorators import post_validated_fields, status, post_data_to_dict
from rest_framework.decorators import api_view
from django.forms.models import model_to_dict
from iuser.models import ExUser
from django.db.models import Q


# Create your views here.

class ServerMenuCategoryViewSet(ModelViewSet):
    """
    服务目录分类操作
    """
    queryset = ServerMenuCategory.objects.all()
    serializer_class = ServerMenuCategorySerializer

    def create(self, request, *args, **kwargs):
        """
        创建服务目录分类
        """
        msg_prefix = "创建服务目录分类 "
        # req_dict = post_data_to_dict(request.data)
        queryset = ServerMenuCategory.objects.all()
        instance_len = len(queryset)
        i = 1
        i += instance_len
        # print i
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            server_menu_instance = serializer.save()

            server_menu_instance.coding = "c%03d" % (i)
            server_menu_instance.save()

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            response = Response({"status": 1, "msg": msg, "data": serializer.data})
            return response


class ServersViewSet(ModelViewSet):
    """
    服务列表操作
    """

    queryset = Servers.objects.all()
    serializer_class = ServersSerializer

    def list(self, request, *args, **kwargs):
        """
        查看服务列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # queryset = self.filter_queryset(self.get_queryset()) # 默认全部都显示
        user_id = request.user.id
        if not user_id:
            return Response({"status": -1, "msg": "查询服务目录失败,当前用户不存在", "data": {}})
        user_obj = ExUser.objects.filter(id=user_id).first()
        group_obj = user_obj.groups.all().first()
        # 显示当前用户组和非冻结的
        queryset = self.filter_queryset(self.get_queryset().filter(groups=group_obj, is_freeze=False))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='get-all-list')
    def get_all_list(self, request, *args, **kwargs):
        """
        查看服务列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        queryset = self.filter_queryset(self.get_queryset())  # 默认全部都显示

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建服务列表
        """
        msg_prefix = "服务列表 "
        req_category = request.data.get('category')
        if not req_category:
            msg = msg_prefix + u"失败, 分类必填"
            return Response({"status": -1, "msg": msg, "data": {}})
        queryset = Servers.objects.filter(category=req_category).all()
        instance_len = len(queryset)
        i = 1
        i += instance_len
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            server_instance = serializer.save()
            server_instance.coding = "s%03d" % (i)
            server_instance.save()

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            response = Response({"status": 1, "msg": msg, "data": serializer.data})
            return response


class PagesViewSet(ModelViewSet):
    """
    服务页面操作
    """
    queryset = Pages.objects.all()
    serializer_class = PagesSerializer

    def create(self, request, *args, **kwargs):
        """
        创建页面列表
        """
        msg_prefix = "创建页面"
        req_server = request.data.get('server')
        bulk_import_number = request.data.get('bulk_import_number')
        if not req_server:
            msg = msg_prefix + u"失败, 服务必填"
            return Response({"status": -1, "msg": msg, "data": {}})
        queryset = Pages.objects.filter(server=req_server).all()
        instance_len = len(queryset)
        i = 1
        i += instance_len
        # print bulk_import_number, type(bulk_import_number)
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            page_instance = serializer.save()
            page_instance.coding = "p%03d" % (i)
            page_instance.save()
            if bulk_import_number:
                int_number = int(bulk_import_number)
                i = 1
                while i <= int_number:
                    obj = Button.objects.create(
                        name=page_instance.coding + "-" + "b%03d" % i,
                        page=page_instance
                    )
                    obj.coding = "b%03d" % i
                    obj.composite_code = page_instance.server.category.coding + \
                                         page_instance.server.coding + page_instance.coding + obj.coding
                    obj.save()
                    i += 1


        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            response = Response({"status": 1, "msg": msg, "data": serializer.data})
            return response


class buttonsViewSet(ModelViewSet):
    """
    页面按钮操作
    """
    queryset = Button.objects.all()
    serializer_class = buttonsSerializer

    def create(self, request, *args, **kwargs):
        """
        创建按钮列表
        """
        msg_prefix = "创建按钮列表"
        # req_dict = post_data_to_dict(request.data)
        req_page = request.data.get('page')

        # print req_page, type(req_page)
        if not req_page:
            msg = msg_prefix + u"失败, 页面必填"
            return Response({"status": -1, "msg": msg, "data": {}})
        p_obj = Pages.objects.filter(id=req_page).first()

        queryset = Button.objects.filter(page=req_page).all()
        instance_len = len(queryset)
        i = 1
        i += instance_len
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            server_instance = serializer.save()
            server_instance.coding = "b%03d" % (i)
            composite_code = p_obj.server.category.coding + p_obj.server.coding + p_obj.coding + server_instance.coding
            server_instance.composite_code = composite_code
            server_instance.save()

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            response = Response({"status": 1, "msg": msg, "data": serializer.data})
            return response


from iworkflow.models import ProcessDefinition, TaskDefinition


class ServerMapWfViewSet(ModelViewSet):
    """
    服务流程映射操作
    """
    queryset = ServerMapWf.objects.all()
    serializer_class = ServerMapWfSerializer

    @action(detail=False, methods=['get'], url_path='get-server-map-list')
    def get_no_parent_id_list(self, request, *args, **kwargs):
        """
        返回一级映射
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # 不包含 二级映射
        queryset = self.filter_queryset(self.get_queryset().filter(parent_id=None))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建服务与流程的映射关系
        """
        msg_prefix = "创建服务与流程的映射关系"
        # req_dict = post_data_to_dict(request.data)
        # synthesize_code = request.data.get('synthesize_code')
        work_flow_key = request.data.get('work_flow_key')
        server_id = request.data.get('server_id')
        page_id = request.data.get('page_id')
        # is_approve = request.data.get('is_approve')
        node_id = request.data.get('node_id')

        # print req_page, type(req_page)
        if not server_id:
            msg = msg_prefix + u"失败, 服务必填"
            return Response({"status": -1, "msg": msg, "data": {}})
        flag = 0  # 来一个标志位，用于标记是不是 子记录 是不是服务详情记录
        if work_flow_key and server_id and page_id and node_id:
            flag = 1
        elif work_flow_key and server_id and page_id:
            flag = 2
        try:

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            server_instance = serializer.save()
            server_obj = Servers.objects.filter(id=server_id).first()
            page_obj = Pages.objects.filter(id=page_id).first()
            node_obj = TaskDefinition.objects.filter(id=node_id).first()
            groups_set = server_obj.groups.all()
            user_list1 = []
            for i in groups_set:
                user_list1.append(i.name)
            if server_obj:
                server_instance.server_id = server_obj.id
                # server_instance.server_name = server_obj.name
            if flag == 1:  # 子记录
                parent_obj = ServerMapWf.objects.filter(work_flow_key=work_flow_key, server_id=server_id).first()
                server_instance.node_id = node_obj.id
                # server_instance.node_name = node_obj.taskName.taskName
                server_instance.page_id = page_obj.id
                # server_instance.page_name = page_obj.name
                server_instance.parent_id = parent_obj.id
                # 先获取第一个页面的按钮
                button_obj = Button.objects.filter(page=page_obj).first()
                server_instance.synthesize_code = button_obj.composite_code
                # 缺少综合编码
            elif flag == 2:  # 详情的子记录
                parent_obj = ServerMapWf.objects.filter(work_flow_key=work_flow_key, server_id=server_id).first()
                server_instance.page_id = page_obj.id
                server_instance.parent_id = parent_obj.id
                button_obj = Button.objects.filter(page=page_obj).first()
                server_instance.synthesize_code = button_obj.composite_code
            server_instance.save()


        #            #     server_instance.coding = "b%03d" % (i)
        #     composite_code = p_obj.server.category.coding + p_obj.server.coding + p_obj.coding + server_instance.coding
        #     server_instance.composite_code = composite_code
        # server_instance.work_flow_key = process_dict
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            msg = msg_prefix + u"成功!"
            response = Response({"status": 1, "msg": msg, "data": serializer.data})
            return response

    @action(detail=False, methods=['post'], url_path='update-note-data')
    def update_note_data(self, request, *args, **kwargs):
        """
        更新子映射
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"更新子映射"
        req_data = request.data
        serverMap_id = req_data.get('serverMap_id')
        node_id = req_data.get('node_id')
        page_id = req_data.get('page_id')
        try:
            page_obj = Pages.objects.filter(id=page_id).first()
            node_obj = TaskDefinition.objects.filter(id=node_id).first()
            instance = ServerMapWf.objects.filter(id=serverMap_id).first()
            instance.node_id = node_id
            instance.node_name = node_obj.taskName.taskName
            instance.page_id = page_obj.id
            instance.page_name = page_obj.name
            instance.save()
            data = model_to_dict(instance)
            # serializer = self.get_serializer(data=instance)
        except Exception, e:
            msg = msg_prefix + u"失败，错误信息：" + unicode(e)
            logger.error(format_exc())
            return Response({'status': -1, 'msg': msg, "data": []})
        else:
            msg = msg_prefix + u"成功"
            return Response({'status': 1, 'msg': msg, "data": data})

    @action(detail=False, methods=['post'], url_path='get-note-and-page')
    def get_note_and_page(self, request, *args, **kwargs):
        """
        获取子映射
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # 发送 一级对应关系
        req_data = request.data
        serverMap_id = req_data.get('parent_id')
        queryset = self.get_queryset().filter(parent_id=serverMap_id).all().exclude(node_id=None).all()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='find-map-relation')
    def find_map_relation(self, request, *args, **kwargs):
        """
        返回对应关系
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        msg_prefix = u"查找对应关系"
        req_dict = post_data_to_dict(request.data)
        category_code = smart_get(req_dict, 'category_code', str)
        page_code = smart_get(req_dict, 'page_code', str)
        service_code = smart_get(req_dict, 'service_code', str)
        button_code = smart_get(req_dict, 'button_code', str)

        try:
            synthesize_code = category_code + service_code + page_code + button_code
            wf_map_ins = self.get_queryset().filter(synthesize_code=synthesize_code).first()
            bp_map_ins = ServerMapBp.objects.filter(synthesize_code=synthesize_code).first()
            data = {}
            if not wf_map_ins and not bp_map_ins:
                msg = msg_prefix + u"失败，"
                logger.error(format_exc())
                return Response({'status': -1, 'msg': msg, "data": []})

            elif wf_map_ins and not bp_map_ins:

                wf_map_dict = model_to_dict(wf_map_ins)
                data['wf_map_relation'] = wf_map_dict
            elif bp_map_ins and not wf_map_ins:

                bp_map_dict = model_to_dict(bp_map_ins)
                data['bp_map_relation'] = bp_map_dict
            else:
                bp_map_dict = model_to_dict(bp_map_ins)
                data['bp_map_relation'] = bp_map_dict
                wf_map_dict = model_to_dict(wf_map_ins)
                data['wf_map_relation'] = wf_map_dict
        except Exception, e:
            msg = msg_prefix + u"失败，错误信息：" + unicode(e)
            logger.error(format_exc())
            return Response({'status': -1, 'msg': msg, "data": []})
        else:
            msg = msg_prefix + u"成功"
            return Response({'status': 1, 'msg': msg, "data": data})

    def get_map_relation(self, request, *args, **kwargs):
        """
        通过编码给
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

    @action(detail=False, methods=['post'], url_path='return-map-relation')
    def return_map_relation(self, request, *args, **kwargs):
        """
        根据流程和服务的关系给出具体页面
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"查找对应关系"
        req_data = request.data
        # print req_data
        try:
            process_info_dict = req_data.get("process_info")
            map_relation_dict = req_data.get("map_relation")
            if not process_info_dict:
                raise Exception("暂无当前流程信息")
            if not map_relation_dict:
                raise Exception("暂无当前映射信息")

            first_task_instance_dict = process_info_dict.get("first_task_instance")
            # task_definition_id = process_info_dict.get("task_definition_id")
            pDefinitionId = first_task_instance_dict.get("pDefinitionId")
            map_relation_parent_id = map_relation_dict.get("parent_id")

            check_approve = req_data.get("check_approve")
            # print pDefinitionId, map_relation_parent_id

            map_ins = ServerMapWf.objects.filter(work_flow_key=str(pDefinitionId), parent_id=map_relation_parent_id,
                                                 node_id=None).first()
            if not map_ins:
                raise Exception("暂无映射对象")

            data = {}
            map_ins_dict = model_to_dict(map_ins)
            data['map_relation'] = map_ins_dict
            data['check_approve'] = check_approve

        except Exception as e:
            msg = msg_prefix + "失败， 错误信息:" + unicode(e)

            return Response({'status': -1, 'msg': msg, "data": []})
        else:
            msg = msg_prefix = "成功"
            return Response({'status': 1, 'msg': msg, "data": data})


class ServerMapBpViewSet(ModelViewSet):
    """
    服务蓝图映射操作
    """
    queryset = ServerMapBp.objects.all()
    serializer_class = ServerMapBpSerializer

    def create(self, request, *args, **kwargs):
        """
        创建蓝图和服务的映射
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"创建蓝图和服务映射"
        req_data = request.data
        blue_print_id = req_data.get("blue_print_id")
        button_id = req_data.get("button_id")
        blue_print_obj = BluePrintDefinition.objects.filter(id=blue_print_id).first()
        button_obj = Button.objects.filter(id=button_id).first()

        try:

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            instance.blue_print_name = blue_print_obj.name
            instance.button_name = button_obj.name
            instance.synthesize_code = button_obj.composite_code
            instance.save()
        except Exception, e:
            logger.error(format_exc())
            msg = msg_prefix + u"失败，错误信息：" + unicode(e)
            logger.error(format_exc())
            return Response({'status': -1, 'msg': msg, "data": []})
        else:
            msg = msg_prefix + u"成功！"
            return Response({'status': 1, 'msg': msg, 'data': serializer.data})


def format_code(category_code, service_code, page_code, button_code=None):
    """
    匹配各种编码，返回一个综合编码
    :param service_code: 
    :param page_code: 
    :param button_code: 
    :return: 
    """
    msg_prefix = u"设置综合编码 "
    p_obj = Pages.objects.filter(
        server__category__coding=category_code,
        server__coding=service_code,
        coding=page_code
    ).first()
    b_obj = Button.objects.filter(page=p_obj, coding=button_code).first()
    try:
        if not button_code:
            data = p_obj.server.category.coding + p_obj.server.coding + p_obj.coding
        elif button_code:
            data = b_obj.page.server.category.coding + b_obj.page.server.coding + b_obj.page.coding + b_obj.coding

    except Exception, e:
        msg = msg_prefix + u"失败，错误信息：" + unicode(e)
        logger.error(format_exc())
        return {'status': -1, 'msg': msg, "data": []}
    else:
        msg = msg_prefix + u"成功！"
        return {'status': 1, 'msg': msg, 'data': data}


@api_view(['POST'])
def get_code(request):
    """

    :param request:
    :return:
    """
    msg_prefix = u'获取编码'
    category_code = request.data.get('category_code')
    page_code = request.data.get('page_code')
    button_code = request.data.get('button_code')
    service_code = request.data.get('service_code')

    req = format_code(category_code=category_code, service_code=service_code, page_code=page_code,
                      button_code=button_code)
    if req['status'] == -1:
        msg = msg_prefix + "失败,设置编码失败"
        return Response({'status': -1, "msg": msg, 'data': req})
    elif req['status'] == 1:
        msg = msg_prefix + "成功"
        data = req['data']
        #  查找对应关系
        page_ins = Pages.objects.filter(coding=page_code).first()
        button_ins = Button.objects.filter(page=page_ins).first()
        if not button_ins:
            return Response({'status': -1, "msg": '不存在的对象', 'data': []})
        server_wf_ins = ServerMapWf.objects.filter(synthesize_code=button_ins.composite_code).first()
        ser_wf = model_to_dict(server_wf_ins)
        dict1 = {
            "synthesize_code": data,
            "server_wf": ser_wf
        }
        # serializer = ServerMapWfSerializer(instance=server_wf_ins)
        # data['server_wf'] = ser_wf
        # req['server_wf'] = serializer.data

        return Response({'status': 1, "msg": msg, 'data': dict1})


class ServerParamsViewSet(ModelViewSet):
    queryset = ServerParams.objects.all()
    serializer_class = ServerParamsSerializer

    # def

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ins = serializer.save()
        # if ins.params_purpose == "PAGE_PARAM":
        #     ins.is_editable = False
        #     ins.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='edit-param')
    def edit_param(self, request, *args, **kwargs):
        """
        编辑参数
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        req_data = request.data
        param_id = req_data.get("param_id")
        edit_params_type = req_data.get("params_type")
        edit_params_purpose = req_data.get("params_purpose")
        edit_params_name = req_data.get("params_name")
        edit_params_name_display = req_data.get("params_name_display")
        edit_param_comment = req_data.get("param_comment")
        ins = self.get_queryset().filter(id=param_id).first()
        if not ins:
            return Response({'status': -1, "msg": "编辑对象不存在", 'data': []})
        ins.params_type = edit_params_type
        ins.params_purpose = edit_params_purpose
        ins.params_name = edit_params_name
        ins.params_name_display = edit_params_name_display
        ins.param_comment = edit_param_comment
        if ins.params_purpose == "PAGE_PARAM":
            ins.is_editable = False
        ins.save()
        serializer = self.get_serializer(ins)
        return Response({'status': 1, "msg": "编辑参数成功", 'data': serializer.data})

    @action(detail=False, methods=['post'], url_path='get-params-list')
    def get_params_list(self, request, *args, **kwargs):
        """
        根据服务ID获取参数列表
        :server_id:
        :return:
        """
        req_data = request.data
        server_id = req_data.get("server_id")
        queryset = self.filter_queryset(self.get_queryset().filter(server_id=server_id))

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_editable:
            return Response({'status': -1, "msg": "此对象不可修改且无法删除", 'data': []})
        instance.delete()
        return Response({'status': 1, "msg": "此对象已删除", 'data': []}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get', 'post'], url_path='get-option-field')
    def get_option_field(self, request, *args, **kwargs):
        """
        获取字段
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        data = {}
        data["PARAMS_PURPOSE_TYPE"] = ServerParams.PARAMS_PURPOSE_TYPE
        data["PAGE_PARAM_TYPE"] = ServerParams.CH_SETTING_TYPE
        data["INTER_FACE_TYPE"] = ServerParams.CH_INTERFACE_TYPE
        if request.method == "GET":
            if not data:
                return Response({"status": -1, 'msg': '错误', "data": []})
            else:
                data1 = dict(data["PARAMS_PURPOSE_TYPE"])
                list1 = []
                for i in data1.items():
                    dict2 = {}
                    dict2[i[0]] = i[1]
                    list1.append(dict2)

                if not list1:
                    return Response({"status": -1, "msg": "失败", "data": []})
                return Response({"status": 1, "msg": "成功", "data": list1})
        if request.method == "POST":
            req_data = request.data
            param_purpose = req_data.get("param_purpose_type")
            if param_purpose in data["PARAMS_PURPOSE_TYPE"][0]:

                data1 = dict(data["PAGE_PARAM_TYPE"])
                list1 = []
                for i in data1.items():
                    dict2 = {}
                    dict2[i[0]] = i[1]
                    list1.append(dict2)
                return Response({"status": 1, "msg": "成功", "data": list1})
            elif param_purpose in data["PARAMS_PURPOSE_TYPE"][1]:
                data1 = dict(data["INTER_FACE_TYPE"])
                list1 = []
                for i in data1.items():
                    dict2 = {}
                    dict2[i[0]] = i[1]
                    list1.append(dict2)
                return Response({"status": 1, "msg": "成功", "data": list1})


class ServerParamValuesViewSet(ModelViewSet):
    queryset = ServerParamValues.objects.all()
    serializer_class = ServerParamValuesSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        server_param_ins = ServerParams.objects.filter(id=instance.param_id).first()
        if not server_param_ins:
            return Response({'status': -1, "msg": "无此对象", 'data': []})
        instance.param_ins = server_param_ins
        instance.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='get-param-values-list')
    def get_param_values_list(self, request):
        """
        通过发送 参数简称或者ID 返回参数值列表
        param_id: 参数ID
        :return: 参数值列表
        """
        req_data = request.data
        params_name = req_data.get("param_name")
        params_id = req_data.get("params_id")
        server_id = req_data.get("server_id")
        if not server_id:
            param_ins = ServerParams.objects.filter(Q(params_name=params_name) | Q(id=params_id)
                                                    ).first()
        else:
            param_ins = ServerParams.objects.filter(Q(params_name=params_name) | Q(id=params_id),
                                                    server_id=server_id).first()

        if not param_ins:
            return Response({'status': -1, "msg": "无此对象", 'data': []})

        queryset = self.filter_queryset(self.get_queryset().filter(param_id=param_ins.id).all())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    #
    # @action(detail=False, methods=['post'], url_path='get-param-values-list')
    # def get_param_values_list(self, request):
    #     """
    #     通过发送 参数ID 返回参数值列表
    #     param_id: 参数ID
    #     :return: 参数值列表
    #     """
    #     req_data = request.data
    #     param_id = req_data.get("param_id")
    #     queryset = ServerParamValues.objects.filter(param_id=param_id).all()
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='show-param-matching')
    def show_param_matching(self, request):
        """
        发送一个参数值ID返回一个匹配规则列表
        param_id: 参数ID
        :return: 参数值列表
        """
        req_data = request.data
        # print req_data
        params_value_id = req_data.get("params_value_id")
        # params_value_id = req_data.get("params_value_id")
        if not params_value_id:
            return Response({'status': -1, "msg": "未输入参数", 'data': []})
        param_value_ins = ServerParamValues.objects.filter(id=params_value_id).first()
        if not param_value_ins:
            return Response({'status': -1, "msg": "无此对象", 'data': []})
        # print  param_ins
        req_queryset = MatchedCondition.objects.filter(matching_param_value_id=param_value_ins.id).all()
        # print req_queryset
        if not req_queryset:
            return Response({'status': -1, "msg": "无此对象组", 'data': []})
        # serializer = self.get_serializer(req_queryset,many=True)
        list1 = []
        for i in req_queryset:
            list2 = i.matching_rule.param_value
            for j in list2:
                param_value_ins = ServerParamValues.objects.filter(id=j).first()
                data = model_to_dict(param_value_ins)

                list1.append(data)
        return Response(list1)

    @action(detail=False, methods=['post'], url_path='edit-param-value')
    def edit_param_value(self, request, *args, **kwargs):
        req_data = request.data
        # param_id = req_data.get("param_id")
        param_value_id = req_data.get("param_value_id")
        edit_param_value_name = req_data.get("param_value_name")
        edit_param_value_tag_name = req_data.get("param_value_tag_name")
        # edit_params_value_type = req_data.get("params_type")
        # edit_params_purpose = req_data.get("params_purpose")
        # edit_params_name = req_data.get("params_name")
        # edit_params_name_display = req_data.get("params_name_display")
        # edit_param_comment = req_data.get("param_comment")
        # param_ins = ServerParams.objects.filter(id=param_id).first()
        param_value_ins = self.get_queryset().filter(id=param_value_id).first()
        if not param_value_ins:
            return Response({'status': -1, "msg": "编辑对象不存在", 'data': []})
        param_value_ins.param_value_name = edit_param_value_name
        param_value_ins.param_value_tag_name = edit_param_value_tag_name
        # ins.params_name = edit_params_name
        # ins.params_name_display = edit_params_name_display
        # ins.param_comment = edit_param_comment
        # if ins.params_purpose == "PAGE_PARAM":
        #     ins.is_editable = False
        param_value_ins.save()
        serializer = self.get_serializer(param_value_ins)
        return Response({'status': 1, "msg": "编辑参数成功", 'data': serializer.data})


# Create your views here.
class PrimaryApplicationViewSet(ModelViewSet):
    """
    一级应用管理操作
    """
    queryset = PrimaryApplication.objects.all()
    serializer_class = PrimaryApplicationSerializer

    def create(self, request, *args, **kwargs):
        """
        创建一级应用
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"创建一级应用"

        queryset = self.get_queryset().all()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance_len = len(queryset)
        i = 1
        i += instance_len
        instance.number = i - 1
        instance.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='get-secondary-app')
    def get_secondary_app(self, request):
        msg_prefix = u"动态获取二级应用"
        req_dict = post_data_to_dict(request.data)
        primary_app_id = smart_get(req_dict, 'id', int)
        app_name = smart_get(req_dict, 'app_name', str)
        app_short_name = smart_get(req_dict, 'app_short_name', str)
        try:
            primary_ins = self.get_queryset().filter(id=primary_app_id).first()
            if not primary_ins:
                msg = msg_prefix + u"失败"
                return Response({"status": -1, "msg": msg, "data": []})
            secondary_set = primary_ins.secondary.all()
            # print secondary_set
            if not secondary_set:
                msg = msg_prefix + u"失败"
                return Response({"status": -1, "msg": msg, "data": []})
            list1 = []
            for i in secondary_set:
                data1 = model_to_dict(i)
                if data1:
                    list1.append(data1)
            # if list1:
            #     return

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}})
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": list1})

    @action(detail=False, methods=['post'], url_path='fuzzy-search')
    def fuzzy_search(self, request):
        """
        模糊搜索
        * 参数
        ** id - 操作系统id
        """
        msg_prefix = u"一级应用模糊搜索"

        search_keyword = request.data.get("search_keyword")

        try:

            first_app_set = self.get_queryset().filter(
                Q(app_name__icontains=search_keyword) | Q(app_short_name__icontains=search_keyword))
            serializer = self.get_serializer(first_app_set, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}})
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})

    @action(detail=False, methods=['post'], url_path='fuzzy-search-test')
    def fuzzy_search_test(self, request):
        """

        :param request:
        :return:
        """
        msg_prefix = u"一级应用模糊搜索"
        req_dict = post_data_to_dict(request.data)
        search_keyword = smart_get(req_dict, 'search_keyword', str)

        try:
            first_app_set = self.get_queryset().filter(app_name__icontains=search_keyword)
            if not first_app_set:
                first_app_set1 = self.get_queryset().filter(app_short_name__icontains=search_keyword)
                if not first_app_set1:
                    return Response({"status": 1, "msg": "暂无数据", "data": []})
                else:
                    serializer = self.get_serializer(first_app_set1, many=True)
            else:
                serializer = self.get_serializer(first_app_set, many=True)

        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}})
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})


class SecondaryApplicationViewSet(ModelViewSet):
    """
    二级应用管理操作
    """
    queryset = SecondaryApplication.objects.all()
    serializer_class = SecondaryApplicationSerializer

    @action(detail=False, methods=['post'], url_path='clone-create')
    def clone_create(self, request, *args, **kwargs):
        """
        用于 除了 应用名称和应用简称之外都和一级应用其他参数一致
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"创建二级应用"
        parent_id = request.data.get("parent_app")
        app_short_name = request.data.get("app_short_name")
        app_name = request.data.get("app_name")
        parent_ins = PrimaryApplication.objects.filter(id=parent_id).first()
        if not parent_ins:
            msg = msg_prefix + u"失败!"
            return Response({"status": -1, "msg": msg, "data": []})
        data = model_to_dict(parent_ins)
        data['parent_app'] = parent_ins.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.app_short_name = app_short_name
        instance.app_name = app_name
        instance.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='fuzzy-search')
    def fuzzy_search(self, request):
        """
        模糊搜索
        * 参数
        ** id - 操作系统id
        """
        msg_prefix = u"二级应用模糊搜索"
        search_keyword = request.data.get("search_keyword")
        try:
            first_app_set = self.get_queryset().filter(
                Q(app_name__icontains=search_keyword) | Q(app_short_name__icontains=search_keyword))

            serializer = self.get_serializer(first_app_set, many=True)
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            return Response({"status": -1, "msg": msg, "data": {}})
        else:
            msg = msg_prefix + u"成功!"
            return Response({"status": 1, "msg": msg, "data": serializer.data})


class ServerMatchingRuleViewSet(ModelViewSet):
    queryset = ServerMatchingRule.objects.all()
    serializer_class = ServerMatchingRuleSerializer

    def create(self, request, *args, **kwargs):
        """
        新建匹配规则
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"新建匹配规则"
        req_dict = request.data
        param_id = req_dict.get("param_id")
        params_value_list1 = req_dict.get("params_value_id")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        param_ins = ServerParams.objects.filter(id=param_id).first()
        if not param_ins:
            return Response({"status": -1, "msg": "无此对象", "data": {}})
        instance.param_of_server_id = param_ins.server_id
        instance.param_value_id = params_value_list1
        instance.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='edit-matching-rule')
    def edit_matching_rule(self, request):
        msg_prefix = u"修改匹配规则"
        req_dict = request.data
        matching_rule_id = req_dict.get("matching_rule_id")

        matching_param_id = req_dict.get("matching_param_id")

        matching_param_value_list = req_dict.get("matching_param_value_id")
        param_pattern = req_dict.get("param_pattern")
        ins = self.get_queryset().filter(id=matching_rule_id).first()
        # param_ins = ServerParams.objects.filter(id=matching_param_id).first()
        ins.param_id = matching_param_id
        ins.param_value_id = matching_param_value_list
        ins.param_matching_pattern = param_pattern
        ins.save()
        serializer = self.get_serializer(instance=ins)

        return Response({"status": 1, "msg": "修改匹配规则成功", "data": serializer.data})


import json


class MatchedConditionViewSet(ModelViewSet):
    queryset = MatchedCondition.objects.all()
    serializer_class = MatchedConditionSerializer

    def create(self, request, *args, **kwargs):
        """
        新建匹配规则
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"新建匹配规则条件"
        req_dict = request.data
        matching_rule_id = req_dict.get("matching_rule_id")
        matching_param_id = req_dict.get("matching_param_id")
        matching_param_value_id = req_dict.get("matching_param_value")
        #
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        match_rule_ins = ServerMatchingRule.objects.filter(id=matching_rule_id).first()
        if not match_rule_ins:
            return Response({"status": -1, "msg": "无此对象", "data": {}})
        matching_param_ins = ServerParams.objects.filter(id=matching_param_id).first()
        if not matching_param_ins:
            return Response({"status": -1, "msg": "无此对象", "data": {}})
        instance.matching_rule = match_rule_ins
        instance.matching_param = matching_param_ins
        instance.matching_param_value_id = matching_param_value_id

        instance.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='edit-matching-condition')
    def edit_matching_condition(self, request):
        """

        :param request:
        :return:
        """
        msg_prefix = u"修改匹配规则条件"
        req_dict = request.data
        # req_dict = request.data
        matching_condition_id = req_dict.get("matching_condition_id")
        matching_param_id = req_dict.get("matching_param_id")
        matching_param_value_id = req_dict.get("matching_param_value")
        # matching_rule_id = req_dict.get("matching_rule_id")
        matching_condition_ins = self.get_queryset().filter(id=matching_condition_id).first()
        # param_value_ins = ServerParamValues.objects.filter(id=matching_param_value_id).first()
        param_ins = ServerParams.objects.filter(id=matching_param_id).first()
        matching_condition_ins.matching_param = param_ins
        matching_condition_ins.matching_param_value_id = matching_param_value_id
        # matching_condition_ins.matching_param_value=param_value_ins.param_value_name
        matching_condition_ins.save()
        # queryset = self.get_queryset().filter(matching_rule=match_rule_ins).all()
        serializer = self.get_serializer(instance=matching_condition_ins)

        return Response({"status": 1, "msg": "修改匹配规则条件成功", "data": serializer.data})

    @action(detail=False, methods=['post'], url_path='get-matching-condition-list')
    def get_matching_condition_list(self, request):
        """

        :param request:
        :return:
        """
        msg_prefix = u"获取匹配规则条件"
        req_dict = request.data
        matching_rule_id = req_dict.get("matching_rule_id")
        match_rule_ins = ServerMatchingRule.objects.filter(id=matching_rule_id).first()
        queryset = self.get_queryset().filter(matching_rule=match_rule_ins).all()
        serializer = self.get_serializer(queryset, many=True)

        return Response({"status": 1, "msg": "获取匹配规则条件成功", "data": serializer.data})

    @action(detail=False, methods=['post'], url_path='obtain-matching-rule-values')
    def obtain_matching_rule_values(self, request):
        """
        获取匹配规则值
        :param request:
        :return:
        """
        msg_prefix = u"获取匹配规则值"
        req_dict = post_data_to_dict(request.data)
        # print req_dict
        # param_id = req_dict.get("param_id")
        param_id = smart_get(req_dict, "param_id", int)
        matching_param_value_id_list = req_dict.get("matching_param_value_id")
        if not matching_param_value_id_list:
            return Response({"status": -1, "msg": "参数值没有ID", "data": []})

        param_matching_pattern = smart_get(req_dict, "param_matching_pattern", str)
        if not param_matching_pattern:
            return Response({"status": -1, "msg": "匹配方式", "data": []})

        int_list = []
        for i in matching_param_value_id_list:
            int_i = int(i)
            int_list.append(int_i)
        if not int_list:
            return Response({"status": -1, "msg": "获取匹配规则失败", "data": []})
        matching_rule_queryset = ServerMatchingRule.objects.filter(param_id=param_id,
                                                                   param_matching_pattern=param_matching_pattern).all()

        if not matching_rule_queryset:
            return Response({"status": -1, "msg": "获取匹配规则失败", "data": []})

        result_list = []
        for i in matching_rule_queryset:
            # 循环出每一个匹配规则对象
            matching_condition_queryset = i.matched_condition.all()
            if not matching_condition_queryset:
                return Response({"status": -1, "msg": "获取匹配规则条件失败", "data": []})
            list1 = []  # [61,64]
            for j in matching_condition_queryset:
                list1.append(j.matching_param_value_id)
            int_list.sort()  # 用户传过来的参数 [64,61,37]
            list1.sort()  # 匹配项中的列表 [64,61]
            set_list = list(set(int_list).intersection(set(list1)))
            set_list.sort()
            #
            # if set_list != list1:
            #     # return Response({"status": -1, "msg": "获取匹配规则条件失败,参数值比对失败", "data": []})
            # result_list = []

            if set_list == list1:
                result_list.append(i)
        # print result_list  #[<ServerMatchingRule: 网络的匹配规则>]

        param_value_id_list = []
        param_value_display_list = []
        if result_list:
            for i in result_list:
                # i.param_value_id "[87]"

                if type(i.param_value_id) != list:
                    load_str_list = json.loads(i.param_value_id)
                    for j in load_str_list:
                        param_value_id_list.append(j)
                else:
                    for j in i.param_value_id:
                        param_value_id_list.append(j)
            for k in param_value_id_list:
                j_ins = ServerParamValues.objects.filter(id=k).first()
                j_ins_serializer = ServerParamValuesSerializer(instance=j_ins)

                param_value_display_list.append(j_ins_serializer.data)
            return Response({"status": 1, "msg": "获取匹配规则条件成功", "data": param_value_display_list})

        else:
            return Response({"status": -1, "msg": "获取匹配规则条件失败", "data": []})
