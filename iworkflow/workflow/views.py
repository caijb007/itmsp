# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
from django.forms.models import model_to_dict
from django.shortcuts import HttpResponse
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from iworkflow.workflow import serializers
from iworkflow import models
from ..business import models as b_models
from iworkflow.models import TaskInstance
from iservermenu.models import ServerMapWf, Button, Pages, Servers
from datetime import  datetime
now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class ProcessCategoryModelView(ModelViewSet):
    """
    流程类型展示和操作类
    注意参数不要写错：
    queryset
    serializer_class
    """
    queryset = models.ProcessCategory.objects.all()
    serializer_class = serializers.ProcessCategorySerializer

    def get_serializer_context(self):
        context = super(ProcessCategoryModelView, self).get_serializer_context()
        return context


class ProcessDefinitionModelView(ModelViewSet):
    """
    流程定义操作类
    """

    def get_serializer_context(self):
        context = super(ProcessDefinitionModelView, self).get_serializer_context()
        return context

    queryset = models.ProcessDefinition.objects.all()
    serializer_class = serializers.ProcessDefinitionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # print serializers
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        task_def_set = instance.task_def.all()
        task_def_list = []
        for i in task_def_set:
            # print i.taskName.taskName
            user_list1 = []
            for j in i.candidate.all():  # 序列化节点定义中的候选人
                user_list1.append(j.id)
            i_data = model_to_dict(i)
            i_data['candidate'] = user_list1
            i_data['task_name'] = i.taskName.taskName
            task_def_list.append(i_data)
        data = model_to_dict(instance)
        data['nodes'] = task_def_list
        return Response(data)


class ProcessTaskNodeModelView(ModelViewSet):
    def get_serializer_context(self):
        context = super(ProcessTaskNodeModelView, self).get_serializer_context()
        return context

    """
    流程节点展示和操作类
    """
    queryset = models.TaskNode.objects.all()
    serializer_class = serializers.ProcessTaskNodeSerializer


class TaskDefinitionModelView(ModelViewSet):
    """
    任务定义展示和操作类
    """

    def get_serializer_context(self):
        context = super(TaskDefinitionModelView, self).get_serializer_context()
        return context

    queryset = models.TaskDefinition.objects.all()
    serializer_class = serializers.ProcessTaskDefinitionSerializer

    @action(detail=False, methods=['post'], url_path='get_user')
    def get_user(self, request):
        definition_id = request.data.get('definition_id')
        t_obj = models.TaskDefinition.objects.filter(id=definition_id).first()
        candidate_set = t_obj.candidate.all()
        l2 = []
        for i in candidate_set:
            # print i.name
            l2.append(i.name)
            # print l2
        # data = model_to_dict(t_obj)
        return Response({'status': 1, 'msg': 'ddd', 'data': []})

    @action(detail=False, methods=['post'], url_path='check-user-permissions')
    def check_user_permissions(self,request,*args,**kwargs):
        """
        检测用户的权限
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        user_id = request.user.id
        """
        "server_wf":{"server_id":"1","parent_id":41,"synthesize_code":"c001s001p001b001","work_flow_key":"3","page_id":1,"id":42,"node_id":7}
        """
        server_wf_dict = request.data.get("server_wf")
        if not server_wf_dict:
            return Response({"status": -1, "msg": "不存在的映射", "data": []})
        node_id= server_wf_dict.get("node_id")

        c_t_obj = models.TaskDefinition.objects.filter(id=node_id).first()
        user_str_list = []
        for user in c_t_obj.candidate.all():
            user_str_list.append(user.id)

        if user_id not in user_str_list:

            msg = u"失败，当前用户无效"
            return Response({"status": -1, "msg": msg, "data": []})
        else:
            return Response({"status": 1, "msg": '有权限', "data": request.data})




class ProcessInstanceModelView(ModelViewSet):
    """
    流程实例展示和操作类
    """

    def get_serializer_context(self):
        context = super(ProcessInstanceModelView, self).get_serializer_context()
        return context

    queryset = models.ProcessInstance.objects.all()
    serializer_class = serializers.ProcessInstanceSerializer

    def retrieve(self, request, *args, **kwargs):

        instance = self.get_object()
        # print instance  # 3
        current_set = TaskInstance.objects.filter(pInstanceId=instance, ).all()
        # print current_set
        l1 = []
        # current_obj = TaskInstance.objects.filter(pInstanceId=instance, taskStatus=1).first()
        # done_obj = instance.processStatus
        # if done_obj == 1:
        if instance.processStatus == 1:
            # return Response({'status':-1, 'msg':"流程已完成",'data':[]})

            data1 = {
                "available_node": "None",
                'currentProcessNodes': "流程已完成"
            }
            data = model_to_dict(instance)
            data.update(data1)
            # if not instance.currentProcessNode.id == current_obj.tDefinitionId.id:
            #     instance.currentProcessNode.id = current_obj.tDefinitionId.id
            #     instance.save()
            return Response(data)
        elif instance.processStatus == 0:
            # 流程仍在进行中

            for i in current_set:

                dict2 = {}

                dict2["id"] = str(i.tDefinitionId.id)
                dict2["name"] = str(i.tDefinitionId.taskName)
                # print i.tDefinitionId.id  # 1 name　2 ip
                # print i.tDefinitionId.taskName
                l1.append(dict2)
            data1 = {
                "available_node": l1,
                # 'currentProcessNodes': str(current_obj.tDefinitionId.taskName)
            }

            data = model_to_dict(instance)
            data.update(data1)

            return Response(data)
        else:
            return Response({"status": 1, "msg": "程序异常", "data": []})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        # def perform_update(self, serializer):
        #     serializer.save()
        #
        # def partial_update(self, request, *args, **kwargs):
        #     kwargs['partial'] = True
        #     return self.update(request, *args, **kwargs)
        # p_obj = self.get_queryset().filter(pk=pk).first()

        instance = self.get_object()
        # print instance
        # print p_obj.currentProcessNode.id
        x_id = request.data.get("currentProcessNode")  # 获取到的是任务的Id
        # print x_id, type(x_id)
        # print x_id
        current_obj = TaskInstance.objects.filter(pInstanceId=instance, taskStatus=1).first()
        if instance.processStatus == 1:
            # return HttpResponse("没有下一步了")
            return Response({"status": -1, "msg": "当前流程已经结束了", "data": []})
        # c_id = current_obj.tDefinitionId.id
        # print p_obj.currentProcessNode.id  # 任务定义的id
        # return Response({"status": 1, "msg": "节点信息错误,当前节点已经更新", "data": []})
        p_c_id = str(instance.currentProcessNode.id)
        c_c_id = str(current_obj.tDefinitionId.id)
        # print p_c_id, type(p_c_id)
        # print c_c_id, type(c_c_id)
        if not (p_c_id == c_c_id):
            # p_obj.currentProcessNode.id = x_id
            p_c_id = c_c_id
            x_obj = TaskInstance.objects.filter(pInstanceId=instance, tDefinitionId=x_id).first()  # x对象
            # print x_obj.id
            lt_obj = TaskInstance.objects.filter(pInstanceId=instance, id__lt=x_obj.id).last()  # x前一个对象, 用于判断是否是开头
            gt_obj = TaskInstance.objects.filter(pInstanceId=instance, id__gt=x_obj.id).first()  # x后一个对象， 用于判断是否是结束
            # print lt_obj,gt_obj
            ex_queryset = TaskInstance.objects.exclude(pInstanceId=instance, id=x_obj.id).all()
            gt_queryset = TaskInstance.objects.filter(pInstanceId=instance, id__gt=x_obj.id).all()
            lt_queryset = TaskInstance.objects.filter(pInstanceId=instance, id__lt=x_obj.id).all()
            # print ex_queryset
            # print gt_queryset
            # print  lt_queryset
            # #
            if x_obj == current_obj:
                pass
            elif x_obj.id > current_obj.id:
                return Response({"status": 1, "msg": "不支持跳转后跳操作", "data": []})

            elif x_obj.id < current_obj.id:
                if not lt_obj:
                    x_obj.taskStatus = 1
                    x_obj.endTime = ''
                    for i in ex_queryset:
                        # 全部状态为已经完成
                        i.taskStatus = 0
                        i.endTime = ''
                        i.save()

                    instance.currentProcessNode.id = x_obj.tDefinitionId.id

                    x_obj.save()
                    instance.save()
                else:
                    x_obj.taskStatus = 1
                    for i in gt_queryset:
                        i.taskStatus = 0
                        i.endTime = ''
                        i.save()
                    instance.currentProcessNode.id = x_obj.tDefinitionId.id
                    x_obj.save()
                    instance.save()
            else:
                return Response({"status": 1, "msg": "操作异常", "data": []})
            # ser_obj = self.get_serializer(instance=p_obj, data=request.data, partial=True)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            # if ser_obj.is_valid():
            #     ser_obj.save()
            #     return Response(ser_obj.data)

            return Response({"status": 1, "msg": "节点信息错误,当前节点已经更新", "data": []})
        #
        # '获取用户选择的节点，我们定为x'
        x_obj = TaskInstance.objects.filter(pInstanceId=instance, tDefinitionId=x_id).first()  # x对象
        # print x_obj.id
        lt_obj = TaskInstance.objects.filter(pInstanceId=instance, id__lt=x_obj.id).last()  # x前一个对象, 用于判断是否是开头
        gt_obj = TaskInstance.objects.filter(pInstanceId=instance, id__gt=x_obj.id).first()  # x后一个对象， 用于判断是否是结束
        # print lt_obj,gt_obj
        ex_queryset = TaskInstance.objects.exclude(pInstanceId=instance, id=x_obj.id).all()
        gt_queryset = TaskInstance.objects.filter(pInstanceId=instance, id__gt=x_obj.id).all()
        lt_queryset = TaskInstance.objects.filter(pInstanceId=instance, id__lt=x_obj.id).all()
        # print ex_queryset
        # print gt_queryset
        # print  lt_queryset
        # #
        if x_obj == current_obj:
            pass
        elif x_obj.id > current_obj.id:
            return Response({"status": -1, "msg": "不支持跳转后跳操作", "data": []})

        elif x_obj.id < current_obj.id:
            if not lt_obj:
                x_obj.taskStatus = 1
                x_obj.startTime = now
                x_obj.endTime = ''
                for i in ex_queryset:
                    # 全部状态为已经完成
                    i.taskStatus = 0
                    i.endTime = ''
                    i.save()

                instance.currentProcessNode.id = x_obj.tDefinitionId.id

                x_obj.save()
                instance.save()
            else:
                x_obj.taskStatus = 1
                x_obj.startTime = now
                for i in gt_queryset:
                    i.taskStatus = 0
                    i.endTime = ''
                    i.save()
                instance.currentProcessNode.id = x_obj.tDefinitionId.id
                x_obj.save()
                instance.save()
        else:
            return Response({"status": -1, "msg": "操作异常", "data": []})
        ser_obj = self.get_serializer(instance=instance, data=request.data, partial=True)
        ser_obj.is_valid(raise_exception=True)
        self.perform_update(ser_obj)
        if ser_obj.is_valid():
            ser_obj.save()
            return Response(ser_obj.data)
        return Response(ser_obj.errors)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # url_path = 'order-list'
    # @action(detail=False, methods=['post'], url_path='process-instance')
    # def process_instance(self, request):
    #     msg_prefix = u"创建流程实例"
    #     #  创建格式化时间前缀
    #     now_time = time.strftime("%Y%m%d", time.localtime())  # 年月日
    #     instance_set = models.ProcessInstance.objects.all()
    #     instance_len = len(instance_set)
    #     i = 1
    #     i += instance_len
    #     k = "%03d" % i
    #     l1 = str(time.time())
    #
    #     instance_name = now_time + l1[-2:] + k
    #
    #     # process_definition_id = request.data.get("process_definition_id")
    #     map_relation_dict = request.data.get("map_relation")
    #
    #     process_definition_id = map_relation_dict.get("work_flow_key")
    #     business_data = request.data.get("business_data")
    #     process_instance_number = request.data.get("process_instance_number")
    #     user_name = request.user
    #
    #     if process_instance_number:
    #         current_process_instance = models.ProcessInstance.objects.filter(
    #             instance_name=process_instance_number).first()
    #         task_instance_obj = TaskInstance.objects.filter(pInstanceId=current_process_instance).order_by('id').first()
    #         if not task_instance_obj:
    #             msg = msg_prefix + u"失败，未生成节点对象,此流程实例不可用"
    #             return Response({'status': -1, 'msg': msg, 'data': []})
    #         task_instance_obj.taskStatus = 1
    #         task_instance_obj.save()
    #
    #         process_instance_id = current_process_instance.id
    #         process_instance_name = current_process_instance.instance_name
    #
    #         first_task_instance = TaskInstance.objects.filter(pInstanceId=current_process_instance).order_by(
    #             'id').first()
    #         # first_log_ins = b_models.WorkflowLog.objects.filter(id=workflow_log_obj.id).first()
    #         first_log_ins = b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_name,
    #                                                             taskInstanceId=first_task_instance).first()
    #         if first_task_instance and first_log_ins:
    #             first_log_ins.business_data = business_data
    #             first_log_ins.updateTime = now
    #             first_log_ins.save()
    #
    #         first_task_instance_dict = model_to_dict(first_task_instance)
    #         data = {
    #             "process_instance": process_instance_id,
    #             "process_instance_number": process_instance_name,
    #             # "taksIntance_id": l1,
    #             'first_task_instance': first_task_instance_dict,
    #             "business_data": business_data,
    #             "map_relation": map_relation_dict
    #         }
    #
    #         msg = msg_prefix + u"成功"
    #         return Response({'status': 1, 'msg': msg, 'data': data})
    #
    #     process_definition_obj = models.ProcessDefinition.objects.filter(id=process_definition_id).first()
    #     if not process_definition_obj:
    #         msg = msg_prefix + u"失败，未生成该对象"
    #         return Response({'status': -1, 'msg': msg, 'data': []})
    #     note_definition_queryset = models.TaskDefinition.objects.filter(pDefinitionId=process_definition_obj).all()
    #     first_note_definition_obj = note_definition_queryset.filter(taskNode=1).first()
    #     if not first_note_definition_obj:
    #         msg = msg_prefix + u"失败，未生成该对象"
    #         return Response({'status': -1, 'msg': msg, 'data': []})
    #     '通过获取到的流程定义 创建流程实例'
    #     create_process_instance = models.ProcessInstance.objects.create(pDefinitionId=process_definition_obj,
    #                                                                     instance_name=instance_name,
    #                                                                     startUserID=user_name,
    #                                                                     currentProcessNode=first_note_definition_obj
    #                                                                     )
    #     if not create_process_instance:
    #         msg = msg_prefix + u"失败"
    #         return Response({'status': -1, 'msg': msg, 'data': []})
    #     process_ins_number = create_process_instance.instance_name
    #     # 创建流程节点实例日志
    #     workflow_log_obj = b_models.WorkflowLog.objects.create(
    #         pInstance_number=process_ins_number,
    #         business_data=business_data,
    #         business_map_relation=map_relation_dict,
    #         creator=create_process_instance.startUserID,
    #     )
    #
    #     if not workflow_log_obj:
    #         msg = msg_prefix + u"失败，未生成日志对象,此流程实例不可用"
    #         models.ProcessInstance.objects.filter(id=create_process_instance.id).delete()
    #         return Response({'status': -1, 'msg': msg, 'data': []})
    #         # '开始创建任务实例'
    #         # "首先要获取任务定义和数量"
    #
    #     task_definition_set = models.TaskDefinition.objects.filter(pDefinitionId=process_definition_obj).order_by(
    #         'taskNode').all()
    #     for task_definition_obj in task_definition_set:
    #         candidate_set = task_definition_obj.candidate.all()
    #         l2 = []
    #         for i in candidate_set:
    #             l2.append(i.name)
    #         TaskInstance.objects.create(pDefinitionId=process_definition_obj,
    #                                     pInstanceId=create_process_instance,
    #                                     taskName=task_definition_obj.taskName.taskName,
    #                                     taskNode=task_definition_obj.taskName,
    #                                     tDefinitionId=task_definition_obj,
    #                                     assignee=l2
    #                                     )
    #         # '已经完成批量化创建，接着就要修改任务节点为1的任务的状态为开启的状态'
    #     task_instance_obj = TaskInstance.objects.filter(pInstanceId=create_process_instance).order_by('id').first()
    #     # print task_instance_obj
    #     # first_log_ins = b_models.WorkflowLog.objects.filter(pInstance_number=create_process_instance.instance_name).first()
    #     first_log_ins = b_models.WorkflowLog.objects.filter(id=workflow_log_obj.id).first()
    #
    #     if task_instance_obj and first_log_ins:
    #         # print "dasdasdasdas"
    #         first_log_ins.taskInstanceId = str(task_instance_obj.id)
    #         first_log_ins.save()
    #         # print "asdasd"
    #     # print str(task_instance_obj.id)
    #     # workflow_log_obj.save()
    #     if not task_instance_obj:
    #         msg = msg_prefix + u"失败，未生成节点对象,此流程实例不可用"
    #         return Response({'status': -1, 'msg': msg, 'data': []})
    #     task_instance_obj.taskStatus = 1
    #     task_instance_obj.save()
    #
    #     # '初始化任务状态已经完毕'
    #     process_instance_id = create_process_instance.id
    #     process_instance_name = create_process_instance.instance_name
    #     task_instance_queryset = TaskInstance.objects.filter(pInstanceId=create_process_instance).order_by('id').all()
    #     first_task_instance = TaskInstance.objects.filter(pInstanceId=create_process_instance).order_by('id').first()
    #
    #     l1 = []
    #     for i in task_instance_queryset:
    #         dict1 = {}
    #         dict1['id'] = str(i.id)
    #         dict1['task_name'] = i.taskName
    #         dict1['task_status'] = i.taskStatus
    #         l1.append(dict1)
    #     first_task_instance_dict = model_to_dict(first_task_instance)
    #     data = {
    #         "process_instance": process_instance_id,
    #         "process_instance_number": process_instance_name,
    #         # "taksIntance_id": l1,
    #         'first_task_instance': first_task_instance_dict,
    #         "business_data": business_data,
    #         "map_relation": map_relation_dict
    #     }
    #
    #     msg = msg_prefix + u"成功"
    #     return Response({'status': 1, 'msg': msg, 'data': data})

    @action(detail=False, methods=['post'], url_path='instance-process')
    def instance_process(self, request):
        msg_prefix = u"保存流程实例"
        #  创建格式化时间前缀
        now_time = time.strftime("%Y%m%d", time.localtime())  # 年月日
        instance_set = models.ProcessInstance.objects.all()
        instance_len = len(instance_set)
        i = 1
        i += instance_len
        k = "%03d" % i
        l1 = str(time.time())

        instance_name = now_time + l1[-2:] + k

        # process_definition_id = request.data.get("process_definition_id")
        map_relation_dict = request.data.get("map_relation")
        process_definition_id = map_relation_dict.get("work_flow_key")
        business_data = request.data.get("business_data")
        # process_instance_number = request.data.get("process_instance_number")
        process_info_dict = request.data.get("process_info")
        user_name = request.user
        if process_info_dict:
            process_instance_number = process_info_dict.get("process_instance_number")
            if process_instance_number:
                current_process_instance = models.ProcessInstance.objects.filter(
                    instance_name=process_instance_number).first()
                task_instance_obj = TaskInstance.objects.filter(pInstanceId=current_process_instance).order_by(
                    'id').first()
                if not task_instance_obj:
                    msg = msg_prefix + u"失败，未生成节点对象,此流程实例不可用"
                    return Response({'status': -1, 'msg': msg, 'data': []})
                # task_instance_obj.taskStatus = 1
                # task_instance_obj.save()

                process_instance_id = current_process_instance.id
                process_instance_name = current_process_instance.instance_name

                first_task_instance = TaskInstance.objects.filter(pInstanceId=current_process_instance).order_by(
                    'id').first()
                first_log_ins = b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_name,
                                                                    taskInstanceId=first_task_instance).first()

                if first_task_instance and first_log_ins:
                    first_log_ins.business_data = business_data
                    first_log_ins.updateTime = now
                    first_log_ins.save()

                first_task_instance_dict = model_to_dict(first_task_instance)
                data = {
                    # "process_instance": process_instance_id,
                    # "process_instance_number": process_instance_name,
                    # # "taksIntance_id": l1,
                    # 'first_task_instance': first_task_instance_dict,
                    # ""
                    "business_data": business_data,
                    "map_relation": map_relation_dict
                }
                data["process_info"] = {'process_instance_number': process_instance_name,
                                        'first_task_instance': first_task_instance_dict,
                                        'task_definition_id': first_task_instance.tDefinitionId.id}

                msg = msg_prefix + u"成功"
                return Response({'status': 1, 'msg': msg, 'data': data})

        process_definition_obj = models.ProcessDefinition.objects.filter(id=process_definition_id).first()
        if not process_definition_obj:
            msg = msg_prefix + u"失败，未生成该对象"
            return Response({'status': -1, 'msg': msg, 'data': []})
        note_definition_queryset = models.TaskDefinition.objects.filter(pDefinitionId=process_definition_obj).all()
        first_note_definition_obj = note_definition_queryset.filter(taskNode=1).first()
        if not first_note_definition_obj:
            msg = msg_prefix + u"失败，未生成该对象"
            return Response({'status': -1, 'msg': msg, 'data': []})
        '通过获取到的流程定义 创建流程实例'
        create_process_instance = models.ProcessInstance.objects.create(pDefinitionId=process_definition_obj,
                                                                        instance_name=instance_name,
                                                                        startUserID=user_name,
                                                                        currentProcessNode=first_note_definition_obj
                                                                        )
        if not create_process_instance:
            msg = msg_prefix + u"失败"
            return Response({'status': -1, 'msg': msg, 'data': []})
        process_ins_number = create_process_instance.instance_name
        # 创建流程节点实例日志
        workflow_log_obj = b_models.WorkflowLog.objects.create(
            pInstance_number=process_ins_number,
            business_data=business_data,
            business_map_relation=map_relation_dict,
            creator=create_process_instance.startUserID,
        )
        if not workflow_log_obj:
            msg = msg_prefix + u"失败，未生成日志对象,此流程实例不可用"
            models.ProcessInstance.objects.filter(id=create_process_instance.id).delete()
            return Response({'status': -1, 'msg': msg, 'data': []})

            # '开始创建任务实例'
            # "首先要获取任务定义和数量"

        task_definition_set = models.TaskDefinition.objects.filter(pDefinitionId=process_definition_obj).order_by(
            'taskNode').all()
        for task_definition_obj in task_definition_set:
            candidate_set = task_definition_obj.candidate.all()
            l2 = []
            for i in candidate_set:
                l2.append(i.name)
            TaskInstance.objects.create(pDefinitionId=process_definition_obj,
                                        pInstanceId=create_process_instance,
                                        taskName=task_definition_obj.taskName.taskName,
                                        taskNode=task_definition_obj.taskName,
                                        tDefinitionId=task_definition_obj,
                                        assignee=l2
                                        )
            # '已经完成批量化创建，接着就要修改任务节点为1的任务的状态为开启的状态'
        task_instance_obj = TaskInstance.objects.filter(pInstanceId=create_process_instance).order_by('id').first()
        # first_log_ins = b_models.WorkflowLog.objects.filter(
        #     pInstance_number=create_process_instance.instance_name).first()
        # if first_log_ins:
        #     first_log_ins.taskInstanceId = str(task_instance_obj.id)
        #     first_log_ins.save()
        first_log_ins = b_models.WorkflowLog.objects.filter(id=workflow_log_obj.id).first()
        # print first_log_ins.id
        # print "qwxzdqw"
        # print lllfirst_log_ins.id
        if task_instance_obj and first_log_ins:
            # print "dasdasdasdas"
            first_log_ins.taskInstanceId = str(task_instance_obj.id)
            first_log_ins.save()
        # print str(task_instance_obj.id)
        # workflow_log_obj.save()
        if not task_instance_obj:
            msg = msg_prefix + u"失败，未生成节点对象,此流程实例不可用"
            return Response({'status': -1, 'msg': msg, 'data': []})
        # task_instance_obj.taskStatus = 1
        # task_instance_obj.save()

        # '初始化任务状态已经完毕'
        process_instance_id = create_process_instance.id
        process_instance_name = create_process_instance.instance_name
        task_instance_queryset = TaskInstance.objects.filter(pInstanceId=create_process_instance).order_by('id').all()
        first_task_instance = TaskInstance.objects.filter(pInstanceId=create_process_instance).order_by('id').first()

        # l1 = []
        # for i in task_instance_queryset:
        #     dict1 = {}
        #     dict1['id'] = str(i.id)
        #     dict1['task_name'] = i.taskName
        #     dict1['task_status'] = i.taskStatus
        #     l1.append(dict1)
        first_task_instance_dict = model_to_dict(first_task_instance)
        # data = {}

        data = {"business_data": business_data, "map_relation": map_relation_dict}

        data["process_info"] = {'process_instance_number': process_instance_name,
                                'first_task_instance': first_task_instance_dict,
                                'task_definition_id': first_task_instance.tDefinitionId.id}

        msg = msg_prefix + u"成功"
        return Response({'status': 1, 'msg': msg, 'data': data})

    @action(detail=False, methods=['post'])
    def process_over(self, request, *args, **kwargs):
        """
        结束任务实例接口
        :param request:
        :param pk:
        :param args:
        :param kwargs:
        :return:
        """
        # print request.data
        process_instance_dict = request.data.get("process_info")
        business_data_dict = request.data.get("business_data")
        map_relation_dict = request.data.get("map_relation")
        if not process_instance_dict:
            return Response({"status": -1, "msg": "暂无输入数据", "data": []})

        process_instance_number = process_instance_dict.get("process_instance_number")

        task_definition_id = process_instance_dict.get("task_definition_id")
        c_t_p_id = task_definition_id

        c_t_p_obj = models.TaskDefinition.objects.filter(id=c_t_p_id).first()
        if not c_t_p_obj:
            return Response({"status": -1, "msg": '无当前任务定义对象', "data": []})

        p_instance_obj = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()
        if not p_instance_obj:
            return Response({"status": -1, "msg": "暂无流程实例", "data": []})
        c_t_obj = TaskInstance.objects.filter(pInstanceId=p_instance_obj,
                                              tDefinitionId=c_t_p_obj).first()  # 当前任务实例
        all_done_task_instance_set = TaskInstance.objects.filter(pInstanceId=p_instance_obj, taskStatus=2).all()
        all_ing_task_instance_set = TaskInstance.objects.filter(pInstanceId=p_instance_obj, taskStatus=1).all()
        all_error_task_instance_set = TaskInstance.objects.filter(pInstanceId=p_instance_obj, taskStatus=3).all()
        if all_done_task_instance_set:
            p_instance_obj.processStatus = 1
            # p_instance_obj.endTime = now
            p_instance_obj.currentProcessNode = c_t_p_obj
            start_time = p_instance_obj.startTime
            start_time = start_time.replace(tzinfo=None)
            end_time = datetime.now()

            p_instance_obj.endTime = end_time
            time_difference_sec = (end_time - start_time).seconds
            p_instance_obj.duration = time_difference_sec
            # current_blue_instance_obj.save()

            # blue_instance_task_obj.task_elapsed_time = time_difference_sec
            p_instance_obj.save()
            # data = model_to_dict(p_instance_obj)

            data = {"business_data": business_data_dict, "map_relation": map_relation_dict}
            first_task_instance_dict = model_to_dict(c_t_obj)
            data["process_info"] = {'process_instance_number': process_instance_number,
                                    'first_task_instance': first_task_instance_dict,
                                    'task_definition_id': task_definition_id}
            return Response({"status": 1, "msg": "节点状态正常，流程已经结束", "data": data})
        elif all_ing_task_instance_set:
            data = model_to_dict(p_instance_obj)
            return Response({"status": -1, "msg": "当前流程不可结束，仍有节点在执行", "data": data})
        elif all_error_task_instance_set:
            data = model_to_dict(p_instance_obj)
            return Response({"status": -1, "msg": "当前流程不可结束，节点有异常", "data": data})
        else:
            data = model_to_dict(p_instance_obj)
            return Response({"status": -1, "msg": "当前流程不可结束，有节点暂未开启", "data": data})

    @action(detail=False, methods=['post'], url_path='revocation-process')
    def revocation_process(self, request):
        """
        my process
        :param request:
        :return:
        """

        msg_prefix = u'撤销流程'

        # user = request.user
        req_data = request.data
        process_instance_number = req_data.get("process_instance_number")
        process_definition_id = req_data.get("process_definition_id")
        try:
            p_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()
            if not p_ins:
                return Response({"status": -1, "msg": "错误,当前流程对象不存在", "data": []})
            t_ins_obj = TaskInstance.objects.filter(pInstanceId=p_ins, tDefinitionId=process_definition_id).first()

            if not t_ins_obj:
                return Response({"status": -1, "msg": "错误,当前映射对象不存在", "data": []})
            # t_data = model_to_dict(t_ins_obj)
            if t_ins_obj.taskStatus != 0:
                return Response({"status": -1, "msg": "错误,当前流程已提交，不可撤销", "data": []})
            elif t_ins_obj.taskStatus == 0:
                b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_number).delete()
                task_instance_queryset = TaskInstance.objects.filter(pInstanceId=p_ins).order_by(
                    'id').all()
                for i in task_instance_queryset:
                    i.delete()
                death_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).delete()
                data = {}
                if death_ins:
                    data['process_instance_number'] = process_instance_number
                    return Response({"status": 1, "msg": "当前流程已被删除", "data": data})

                elif not p_ins:
                    return Response({"status": -1, "msg": "当前流程未被删除", "data": []})
        except Exception, e:
            msg = msg_prefix + u"失败， 错误信息如下:" + unicode(e)
            return Response({"status": -1, "msg": msg, "data": []})

    @action(detail=False, methods=['post'], url_path='test-interface')
    def test_interface(self, request):
        """

        :param request:
        :return:
        """
        req_data = request.data

        return Response({"status": 1, "msg": "接受成功", "data": req_data})

    @action(detail=False, methods=['get'], url_path='my-process')
    def my_process(self, request):
        """
        my process
        :param request:
        :return:
        """

        msg_prefix = u'获取我的流程'

        user = request.user

        try:
            user_data_set = self.get_queryset().filter(startUserID=user)
        except Exception, e:
            msg = msg_prefix + u"失败， 错误信息如下:" + unicode(e)
            return Response({"status": -1, "msg": msg, "data": []})
        else:
            msg = msg_prefix + u"成功！"
            serializer = self.get_serializer(instance=user_data_set, many=True)
        return Response({"status": 1, "msg": msg, "data": serializer.data})

    @action(detail=False, methods=['get'], url_path='approve-process')
    def approve_process(self, request):
        """
        my process
        :param request:
        :return:
        """
        """
        首先要根據用戶來返回他的信息
        """
        msg_prefix = u'获取我的审批'

        user = request.user
        str_user = str(user)

        try:
            all_process_set = self.get_queryset()

            ins_list = [] # 用户过滤
            # ing_ins_list = [] # 流程状态过滤
            fin_ins_list = [] # 流程实例状态过滤， 最终过滤的列表
            for i in all_process_set:
                user_list = []
                for k in i.task_instance.all():
                    if k.assignee:
                        user_list.extend(k.assignee)
                if str_user in user_list:
                    ins_list.append(i)
            # for ins in ins_list:
            #     if ins.processStatus !=1:
            #         ing_ins_list.append(ins)
            # for ing_ins  in ing_ins_list:
            for ing_ins  in ins_list:
                l2 = []
                task_ins_set = ing_ins.task_instance.all()
                for k in task_ins_set:
                    l2.append(k.taskStatus)
                set_status = set(l2)
                set0 = {0}
                if set_status != set0: # 只是不要没有提交的数据
                    fin_ins_list.append(ing_ins)

            serializer = self.get_serializer(instance=fin_ins_list, many=True)

        except Exception, e:
            msg = msg_prefix + u"失败， 错误信息如下:" + unicode(e)
            return Response({"status": -1, "msg": msg, "data": []})
        else:
            msg = msg_prefix + u"成功！"
            return Response({"status": 1, "msg": msg, "data": serializer.data})



    @action(detail=False, methods=['post'], url_path='find-my-approval-detail')
    def find_my_approval_detail(self, request, *args, **kwargs):
        """
        通过服务目录中的映射关系找到我的流程所对应的页面
        :process_instance_number: 流程编号
        :process_definition_id:
        :param kwargs:
        :return:
        """

        req_data = request.data
        process_instance_number = req_data.get("process_instance_number")
        # process_definition_id = req_data.get("process_definition_id")
        p_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()
        if not p_ins:
            return Response({"status": -1, "msg": "错误,当前映射对s象不存在", "data": []})
        # t_ins_obj = TaskInstance.objects.filter(pInstanceId=p_ins, tDefinitionId=process_definition_id).first()
        # print t_ins_obj
        # if not t_ins_obj:
        #     return Response({"status": -1, "msg": "错误,当前映射对象不存在", "data": []})
        business_log_ins = b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_number,
                                                               intervene_type_id=0).first()
        # print business_log_ins.id
        if not business_log_ins:
            return Response({"status": -1, "msg": "错误,当前映射ssss对象不存在", "data": []})
        business_map_relation_dict = business_log_ins.business_map_relation
        if not business_map_relation_dict:
            return Response({"status": -1, "msg": "错误,当前映射关系不存在", "data": []})
        synthesize_code = business_map_relation_dict.get("synthesize_code")
        log_ins = ServerMapWf.objects.filter(synthesize_code=synthesize_code).first()
        data = {}
        if not log_ins:
            return Response({"status": -1, "msg": "错误,当前日志对象不存在", "data": []})
        # server_id = server_ins.server_id
        task_ins = TaskInstance.objects.filter(id=business_log_ins.taskInstanceId).first()
        if not task_ins:
            return Response({"status": -1, "msg": "错误,当前日志对象不存在", "data": []})
        task_ins_dict = model_to_dict(task_ins)
        data['map_relation'] = model_to_dict(log_ins)
        data['business_data'] = business_log_ins.business_data

        data["process_info"] = {'process_instance_number': p_ins.instance_name,
                                'first_task_instance': task_ins_dict,
                                'task_definition_id': task_ins.tDefinitionId.id}
        # data['process_task_info'] = task_ins_dict
        return Response({"status": 1, "msg": "成功", "data": data})

    @action(detail=False, methods=['post'], url_path='find-process-server-page')
    def find_process_server_page(self, request, *args, **kwargs):
        """
        通过服务目录中的映射关系找到我的流程所对应的页面
        :process_instance_number: 流程编号
        :process_definition_id:
        :param kwargs:
        :return:
        """

        req_data = request.data
        process_instance_number = req_data.get("process_instance_number")
        process_definition_id = req_data.get("process_definition_id")
        p_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()
        if not p_ins:
            return Response({"status": -1, "msg": "错误,当前映射对象不存在", "data": []})
        t_ins_obj = TaskInstance.objects.filter(pInstanceId=p_ins, tDefinitionId=process_definition_id).first()
        print t_ins_obj
        if not t_ins_obj:
            return Response({"status": -1, "msg": "错误,当前映射对象不存在", "data": []})
        business_log_ins = b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_number,
                                                               intervene_type_id=0).first()
        # print business_log_ins.id

        if not business_log_ins:
            return Response({"status": -1, "msg": "错误,当前映射对象不存在", "data": []})
        # business_map_relation_dict = business_log_ins.business_map_relation
        # if not business_map_relation_dict:
        #     return Response({"status": -1, "msg": "错误,当前映射关系不存在", "data": []})
        # synthesize_code = business_map_relation_dict.get("synthesize_code")
        # log_ins = ServerMapWf.objects.filter(synthesize_code=synthesize_code).first()
        log_ins = ServerMapWf.objects.filter(node_id=process_definition_id,
                                             work_flow_key=str(p_ins.pDefinitionId.id)).first()
        data = {}
        if not log_ins:
            return Response({"status": -1, "msg": "错误,当前日志对象不存在", "data": []})
        # server_id = server_ins.server_id
        task_ins = TaskInstance.objects.filter(id=business_log_ins.taskInstanceId).first()
        if not task_ins:
            return Response({"status": -1, "msg": "错误,当前日志对象不存在", "data": []})
        # task_ins_dict = model_to_dict(task_ins)
        data['map_relation'] = model_to_dict(log_ins)
        task_ins_dict = model_to_dict(t_ins_obj)

        data['business_data'] = business_log_ins.business_data
        # data['process_task_info'] = task_ins_dict

        data["process_info"] = {'process_instance_number': p_ins.instance_name,
                                'first_task_instance': task_ins_dict,
                                'task_definition_id': t_ins_obj.tDefinitionId.id}
        return Response({"status": 1, "msg": "成功", "data": data})

    @action(detail=False, methods=['post'], url_path='show-my-approval-approve-info')
    def show_my_approval_approve_info(self, request, *args, **kwargs):
        """
        查看我的流程的审批详情
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u'获取申请者的审批流程的审批详情'
        req_data = request.data
        process_instance_number = req_data.get('process_instance_number')
        task_definition_id = req_data.get("task_definition_id")
        data = {}
        try:
            process_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()
            if not process_ins:
                msg = msg_prefix + "失败，无此对象"
                return Response({"status": -1, "msg": msg, "data": []})
            task_definition_ins = models.TaskDefinition.objects.filter(id=task_definition_id).first()
            task_ins = TaskInstance.objects.filter(pInstanceId=process_ins,
                                                   tDefinitionId=task_definition_ins).first()
            if not task_ins:
                msg = msg_prefix + "失败，无此对象"
                return Response({"status": -1, "msg": msg, "data": []})

            workflow_log_ins = b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_number,
                                                                   taskInstanceId=task_ins).first()

            if not workflow_log_ins:
                msg = msg_prefix + "失败，无此对象"
                return Response({"status": -1, "msg": msg, "data": []})

            task_ins_dict = model_to_dict(task_ins)
            business_data_dict = workflow_log_ins.business_data
            swf_ins = ServerMapWf.objects.filter(work_flow_key=str(process_ins.pDefinitionId.id),node_id=task_definition_id).first()
            if not swf_ins:

                return Response({"status": -1, "msg": "不存在的映射关系", "data": []})
            # map_relation_dict = workflow_log_ins.business_map_relation
            map_relation_dict = model_to_dict(swf_ins)
            if process_ins.processStatus == 0: # 进行中
                data['check_approve'] = 1 #
            elif process_ins.processStatus == 1: # 完成
                data['check_approve'] = 2 #
            elif process_ins.processStatus == 2: #异常
                data['check_approve'] = 0 #

            data["process_info"] = {'process_instance_number': process_ins.instance_name,
                                    'first_task_instance': task_ins_dict,
                                    'task_definition_id': task_ins.tDefinitionId.id}
            # data["business_data"] = business_data_dict
            data["map_relation"] =map_relation_dict


            if not data:
                msg = msg_prefix + "失败，无数据"
                return Response({"status": -1, "msg": msg, "data": []})
        except Exception, e:
            msg = msg_prefix + "失败，错误信息：" + unicode(e)
            return Response({"status": -1, "msg": msg, "data": []})
        else:
            msg = msg_prefix + "成功"

            return Response({"status": 1, "msg": msg, "data": data})

    @action(detail=False, methods=['post'], url_path='show-approve-info')
    def show_approve_info(self, request, *args, **kwargs):
        """
        查看我的流程的审批详情
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u'获取审批者的审批详情'
        req_data = request.data
        process_instance_number = req_data.get('process_instance_number')
        task_definition_id = req_data.get("task_definition_id")
        data = {}
        try:
            process_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()
            if not process_ins:
                msg = msg_prefix + "失败，无此流程"
                return Response({"status": -1, "msg": msg, "data": []})
            task_definition_ins = models.TaskDefinition.objects.filter(id=task_definition_id).first()
            task_ins = TaskInstance.objects.filter(pInstanceId=process_ins,
                                                   tDefinitionId=task_definition_ins).first()
            if not task_ins:
                msg = msg_prefix + "失败，无此任务实例对象"
                return Response({"status": -1, "msg": msg, "data": []})

            workflow_log_ins = b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_number,
                                                                   taskInstanceId=task_ins).first()

            if not workflow_log_ins:
                msg = msg_prefix + "失败，无此流程日志对象"
                return Response({"status": -1, "msg": msg, "data": []})

            task_ins_dict = model_to_dict(task_ins)
            business_data_dict = workflow_log_ins.business_data
            swf_ins = ServerMapWf.objects.filter(work_flow_key=str(process_ins.pDefinitionId.id),node_id=task_definition_id).first()
            if not swf_ins:

                return Response({"status": -1, "msg": "不存在的映射关系", "data": []})
            # map_relation_dict = workflow_log_ins.business_map_relation
            map_relation_dict = model_to_dict(swf_ins)
            if process_ins.processStatus == 0: # 进行中
                data['check_approve'] = 1 #
            elif process_ins.processStatus == 1: # 完成
                data['check_approve'] = 2 #
            elif process_ins.processStatus == 2: #异常
                data['check_approve'] = 3 #
                data["business_data"] = business_data_dict
                data["blue_print_info"] =workflow_log_ins.business_blue_info

            data["process_info"] = {'process_instance_number': process_ins.instance_name,
                                    'first_task_instance': task_ins_dict,
                                    'task_definition_id': task_ins.tDefinitionId.id}

            data["map_relation"] =map_relation_dict


            if not data:
                msg = msg_prefix + "失败，无数据"
                return Response({"status": -1, "msg": msg, "data": []})
        except Exception, e:
            msg = msg_prefix + "失败，错误信息：" + unicode(e)
            return Response({"status": -1, "msg": msg, "data": []})
        else:
            msg = msg_prefix + "成功"

            return Response({"status": 1, "msg": msg, "data": data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        process_ins_number = instance.instance_name
        process_log_ins_set = b_models.WorkflowLog.objects.filter(pInstance_number=process_ins_number).all()
        if not process_log_ins_set:
            return Response({"status": -1, "msg": "无此流程日志记录", "data": []})
        for i in process_log_ins_set:
            i.delete()
        task_ins_set = TaskInstance.objects.filter(pInstanceId=instance).all()
        if not task_ins_set:
            return Response({"status": -1, "msg": "无此流程任务实例", "data": []})
        for i in task_ins_set:
            i.delete()
        is_delete = instance.delete()
        if is_delete:
            return Response({"status": 1, "msg": "此流程已经删除", "data": process_ins_number})
        else:
            return Response({"status": -1, "msg": "无此流程任务实例", "data": []})


class TaskInstanceModelView(ModelViewSet):
    """
    任务实例展示和操作类
    """
    queryset = models.TaskInstance.objects.all()
    serializer_class = serializers.TaskInstanceSerializer

    def get_serializer_context(self):
        context = super(TaskInstanceModelView, self).get_serializer_context()
        return context

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # print instance
        instance_name = instance.pInstanceId.instance_name
        process_definition_obj = instance.pDefinitionId
        task_definition_obj = instance.tDefinitionId
        category_name = process_definition_obj.pCategoryKey.processCategoryName
        definition_name = process_definition_obj.processDefinitionName
        candidate_set = task_definition_obj.candidate.all()
        # print candidate_set
        l1 = []

        for i in candidate_set:
            dict2 = {}

            dict2["id"] = str(i.id)
            dict2["name"] = i.name
            # serializer.data
            l1.append(dict2)

        data1 = {
            'category_name': category_name,
            'definition_name': definition_name,
            "candidate": l1,
            "instance_name": instance_name,
        }
        from django.forms.models import model_to_dict
        data = model_to_dict(instance)
        data.update(data1)

        return Response({"status": 1, "msg": "查看任务实例成功", "data": data})

    @action(detail=False, methods=['post'])
    def agree_interface(self, request, *args, **kwargs):
        """
        同意 按钮操作
        需要补充日志的映射business_map_relation=map_relation_dict,
        :param request:
        :param pk:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"节点同意 按钮操作"
        # print request.data, type(request.data)
        map_relation_dict = request.data.get("map_relation")  # 映射信息
        # process_info_dict = request.data.get("process_info")  # 映射信息
        # if not map_relation_dict:
        #     msg = msg_prefix + u"失败，当前映射关系无效"
        #     return Response({"status": -1, "msg": msg, "data": []})

        # task_definition_id = map_relation_dict.get("node_id")
        # c_t_p_id = request.data.get("task_id")
        business_data_dict = request.data.get("business_data")  # 没有就默认为空字典
        blue_print_info_dict = request.data.get("blue_print_info")  # 没有就默认为空字典
        if not business_data_dict:
            return Response({"status": -1, "msg": '没有业务数据', "data": []})
        process_instance_dict = request.data.get("process_info")
        process_instance_number = process_instance_dict.get("process_instance_number")
        task_definition_id = process_instance_dict.get("task_definition_id")
        c_t_p_id = task_definition_id

        # print request.user
        # c_t_id = request.data.get("task_instance_id")
        # suggestion = request.data.get("suggestion")  # 需要定死这个字段和格式?
        submit_data_dict = business_data_dict.get("submit_data")  # 需要定死这个字段和格式?
        if not submit_data_dict:
            return Response({"status": -1, "msg": '没有业务信息', "data": []})
        submit_info_dict = submit_data_dict.get("submit_info")
        business_submit_advice = submit_info_dict.get("submit_advice")
        user = request.user
        user_id = request.user.id

        c_t_p_obj = models.TaskDefinition.objects.filter(id=c_t_p_id).first()
        if not c_t_p_obj:
            return Response({"status": -1, "msg": '无当前任务定义对象', "data": []})
        c_p_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()  # 当前流程实例
        if not c_p_ins:
            return Response({"status": -1, "msg": '无当前蓝图对象', "data": []})
        c_t_obj = TaskInstance.objects.filter(pInstanceId=c_p_ins,
                                              tDefinitionId=c_t_p_obj).first()  # 当前任务实例
        user_str_list = []
        for user in c_t_obj.assignee:
            user_str_list.append(user_id)

        if user_id not in user_str_list:

            msg = msg_prefix + u"失败，当前用户无效"
            return Response({"status": -1, "msg": msg, "data": []})
        # if c_t_obj.taskStatus == 2 or c_t_obj.taskStatus == 3:
        #     msg = msg_prefix + u"失败，无法审批当前节点"
        #     return Response({"status": -1, "msg": msg, "data": []})
        if not c_t_obj:
            msg = msg_prefix + u"失败，无法获取当前对象"
            return Response({"status": -1, "msg": msg, "data": []})
        c_p_obj = c_t_obj.pInstanceId
        if c_p_obj.processStatus == 1:
            # return HttpResponse("没有下一步了")
            msg = msg_prefix + u"失败，没有下一步了"
            return Response({"status": -1, "msg": msg, "data": []})
        if not (c_p_obj.currentProcessNode.id == c_t_obj.tDefinitionId.id):
            msg = msg_prefix + u"失败，节点信息错误,节点位置已经更新"
            c_p_obj.currentProcessNode = c_t_obj.tDefinitionId
            c_p_obj.save()
            return Response({"status": -1, "msg": msg, "data": []})
        last_task_instance_obj = TaskInstance.objects.filter(pInstanceId=c_p_obj).all().last()
        # print " 最后的接口"
        # print last_task_instance_obj
        while 1:
            "如果是最后一个任务，就直接修改任务状态和流程状态"
            if last_task_instance_obj == c_t_obj:
                # if last_task_instance_obj.taskStatus == 1 and c_p_obj.processStatus == 0:
                if c_p_obj.processStatus != 1: #只要不是已完成，都可以修改
                    last_task_instance_obj.taskStatus = 2  # 执行成功
                    last_task_instance_obj.endTime = now  # 执行成功
                    last_task_instance_obj.save()
                    b_models.WorkflowLog.objects.create(
                        pInstance_number=c_p_obj.instance_name,
                        suggestion=business_submit_advice,
                        participant=user,
                        taskInstanceId=last_task_instance_obj.id,
                        intervene_type_id=1,
                        business_data=business_data_dict,
                        business_map_relation=map_relation_dict,
                        creator=c_p_obj.startUserID,
                        business_blue_info=blue_print_info_dict
                    )
                    task_ins_dict = model_to_dict(last_task_instance_obj)
                    # "后面要独立出来"
                    data = {}
                    data["process_info"] = {'process_instance_number': c_p_obj.instance_name,
                                            'first_task_instance': task_ins_dict,
                                            'task_definition_id': last_task_instance_obj.tDefinitionId.id}
                    data["business_data"] = business_data_dict
                    data["map_relation"] = map_relation_dict
                    msg = msg_prefix + u"成功，最后一个节点执行完成，请确定关闭流程"
                    return Response({"status": 1, "msg": msg, "data": data})
            else:
                # 如果他就是普通的节点
                # task_ins_obj1 = TaskInstance.objects.filter(pInstanceId=c_p_obj, taskStatus=1).first()
                b_models.WorkflowLog.objects.create(
                    pInstance_number=c_p_obj.instance_name,
                    suggestion=business_submit_advice,
                    participant=user,
                    taskInstanceId=c_t_obj.id,
                    intervene_type_id=1,
                    business_data=business_data_dict,
                    business_map_relation=map_relation_dict,
                    creator=c_p_obj.startUserID,
                    business_blue_info=blue_print_info_dict
                )
                c_t_obj.taskStatus = 2  # 执行成功
                c_t_obj.endTime = now  # 执行成功

                c_t_obj.save()
                task_ins_obj2 = TaskInstance.objects.filter(pInstanceId=c_p_obj, taskStatus=0).first()
                task_ins_obj2.taskStatus = 1
                task_ins_obj2.startTime = now
                task_ins_obj2.save()
                c_p_obj.currentProcessNode = task_ins_obj2.tDefinitionId
                c_p_obj.save()
                break
        task_ins_dict = model_to_dict(c_t_obj)
        data = {}
        data["process_info"] = {'process_instance_number': c_p_obj.instance_name,
                                'first_task_instance': task_ins_dict,
                                'task_definition_id': c_t_obj.tDefinitionId.id}
        data["business_data"] = business_data_dict
        data["map_relation"] = map_relation_dict
        msg = msg_prefix + u"成功，该节点已经完成， 进入下一个流程状态~"
        return Response({"status": 1, "msg": msg, "data": data})

    @action(detail=False, methods=['post'])
    def refuse_interface(self, request, *args, **kwargs):
        """
        拒绝 按钮操作
        :param request:
        :param pk:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"节点实例拒绝操作"

        """
        "process_info": {
            "process_instance_number": "2019072624007",
            "first_task_instance": {},
            "task_definition_id": 8
        """
        process_info_dict = request.data.get("process_info")
        business_data_dict = request.data.get("business_data")
        map_relation_dict = request.data.get("map_relation")
        # blue_print_info_dict = request.data.get("business_blue_info")
        if not process_info_dict:
            msg = msg_prefix + u"失败，无流程数据"
            return Response({"status": -1, "msg": msg, "data": []})
        if not business_data_dict:
            msg = msg_prefix + u"失败，无业务数据"
            return Response({"status": -1, "msg": msg, "data": []})
        c_t_p_id = process_info_dict.get("task_definition_id")

        process_instance_number = process_info_dict.get("process_instance_number")
        submit_data_dict = business_data_dict.get("submit_data")  # 需要定死这个字段和格式?
        if not submit_data_dict:
            return Response({"status": -1, "msg": '没有业务信息', "data": []})
        submit_info_dict = submit_data_dict.get("submit_info")
        business_submit_advice = submit_info_dict.get("submit_advice")
        # print request.user
        # c_t_id = request.data.get("task_instance_id")
        # suggestion = request.data.get("suggestion")
        # business_data = request.data.get("business_data")
        user = request.user
        str_user = str(user)
        c_t_p_obj = models.TaskDefinition.objects.filter(id=c_t_p_id).first()
        # print c_t_p_obj
        c_p_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()
        print c_p_ins
        c_t_obj = TaskInstance.objects.filter(pInstanceId=c_p_ins,
                                              tDefinitionId=c_t_p_obj).first()  # 当前任务实例
        if not c_t_obj:
            msg = msg_prefix + u"失败，当前对象无效"
            return Response({"status": -1, "msg": msg, "data": []})
        if str_user not in c_t_obj.assignee:
            msg = msg_prefix + u"失败，当前用户无效"
            return Response({"status": -1, "msg": msg, "data": []})
        if c_t_obj.taskStatus != 1:
            msg = msg_prefix + u"失败，无法审批当前节点"
            return Response({"status": -1, "msg": msg, "data": []})

        # c_t_id = request.data.get("task_instance_id")
        # print c_t_id
        # c_t_obj = TaskInstance.objects.filter(id=c_t_id).first()  # 当前任务实例
        c_p_obj = c_t_obj.pInstanceId  # 当前流程实例
        if c_p_obj.processStatus == 1:
            # return HttpResponse("没有下一步了")
            return Response({"status": 1, "msg": "操作无效,流程已经结束了", "data": []})
        elif c_p_obj.processStatus == 2:
            return Response({"status": 1, "msg": "操作无效,流程异常了", "data": []})
        if not (c_p_obj.currentProcessNode.id == c_t_obj.tDefinitionId.id):
            c_p_obj.currentProcessNode = c_t_obj.tDefinitionId
            c_p_obj.save()
            return Response({"status": 1, "msg": "节点信息错误,节点位置已经更新", "data": []})
        last_taskinstance_obj = TaskInstance.objects.filter(pInstanceId=c_p_obj).all().last()
        first_t_obj = TaskInstance.objects.filter(pInstanceId=c_p_obj).all().first()
        lt_obj = TaskInstance.objects.filter(pInstanceId=c_p_obj, id__lt=c_t_obj.id).last()  # x前一个对象, 用于判断是否是开头
        gt_obj = TaskInstance.objects.filter(pInstanceId=c_p_obj, id__gt=c_t_obj.id).first()  # x后一个对象， 用于判断是否是结束
        while 1:
            if c_t_obj == first_t_obj:  # 如果是第一个节点
                c_t_obj.taskStatus = 0  # 任务执行失败
                # c_t_obj.s = now  # 执行成功
                c_t_obj.save()
                b_models.WorkflowLog.objects.create(
                    pInstance_number=c_p_obj.instance_name,
                    suggestion=business_submit_advice,
                    participant=str_user,
                    taskInstanceId=c_t_obj.id,
                    intervene_type_id=1,
                    business_data=business_data_dict,
                    creator=c_p_obj.startUserID,
                    # business_blue_info=blue_print_info_dict
                )
                c_p_obj.processStatus = 2  # 流程标记异常
                c_p_obj.currentProcessNode = None
                c_p_obj.save()
                data = model_to_dict(c_p_obj)
                # "后面要独立出来"
                return Response({"status": 1, "msg": "收到拒绝请求，当前流程已经关闭,请重新申请流程", "data": data})
            else:

                c_t_obj.taskStatus = 0  # 执行失败
                c_t_obj.startTime = None
                lt_obj.taskStatus = 0  # 修改上一个状态 # 改成0  让用户重新提交
                lt_obj.endTime = None
                c_t_obj.save()
                b_models.WorkflowLog.objects.create(
                    pInstance_number=c_p_obj.instance_name,
                    suggestion=business_submit_advice,
                    participant=str_user,
                    taskInstanceId=c_t_obj.id,
                    intervene_type_id=1,
                    business_data=business_data_dict,
                    creator=c_p_obj.startUserID
                )
                lt_obj.save()
                # task_ins_obj1 = TaskInstance.objects.filter(pInstanceId=c_p_obj, taskStatus=1).first()
                # # print task_ins_obj1
                # task_ins_obj1.taskStatus = 2  # 执行成功
                # task_ins_obj1.endTime = now  # 执行成功
                # task_ins_obj2 = TaskInstance.objects.filter(pInstanceId=c_p_obj, taskStatus=0).first()
                # task_ins_obj2.taskStatus = 1
                # task_ins_obj2.startTime = now
                # task_ins_obj2.save()
                # task_ins_obj1.save()
                c_p_obj.currentProcessNode = lt_obj.tDefinitionId
                c_p_obj.save()
                break
        task_ins_dict = model_to_dict(lt_obj)

        data = {}
        data["process_info"] = {'process_instance_number': c_p_obj.instance_name,
                                'first_task_instance': task_ins_dict,
                                'task_definition_id': c_t_obj.tDefinitionId.id}
        data["business_data"] = business_data_dict
        data["map_relation"] = map_relation_dict
        return Response({"status": 1, "msg": "该节点已经被拒绝， 任务退回到上一个节点~", "data": data})

    @action(detail=False, methods=['post'], url_path='process-ins-error')
    def process_ins_error(self, request, *args, **kwargs):
        """
        流程异常接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        """
        考虑2中情况
             接受到的流程和任务都置位异常状态
        """
        map_relation_dict = request.data.get("map_relation")
        process_instance_dict = request.data.get("process_info")
        business_data_dict = request.data.get("business_data")
        blue_print_info_dict = request.data.get("blue_print_info")
        if not process_instance_dict:
            return Response({"status": -1, "msg": "无流程信息~", "data": []})
        if not business_data_dict:
            return Response({"status": -1, "msg": "无业务信息~", "data": []})
        process_instance_number = process_instance_dict.get("process_instance_number")
        task_definition_id = process_instance_dict.get("task_definition_id")
        c_t_p_id = task_definition_id

        # print request.user
        # c_t_id = request.data.get("task_instance_id")
        # suggestion = request.data.get("suggestion")  # 需要定死这个字段和格式?
        submit_data_dict = business_data_dict.get("submit_data")  # 业务数据字端
        if not submit_data_dict:
            return Response({"status": -1, "msg": '没有业务信息', "data": []})
        submit_info_dict = submit_data_dict.get("submit_info")
        business_submit_advice = submit_info_dict.get("submit_advice")
        user = request.user
        str_user = str(user)
        c_t_p_obj = models.TaskDefinition.objects.filter(id=c_t_p_id).first()
        if not c_t_p_obj:
            return Response({"status": -1, "msg": '无当前任务定义对象', "data": []})
        c_p_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()  # 当前流程实例
        if not c_p_ins:
            return Response({"status": -1, "msg": '无当前蓝图对象', "data": []})
        c_t_obj = TaskInstance.objects.filter(pInstanceId=c_p_ins,
                                              tDefinitionId=c_t_p_obj).first()  # 当前任务实例

        if c_p_ins.processStatus == 1:

            return Response({"status": -1, "msg": "操作无效,流程已经结束了", "data": []})
        elif c_p_ins.processStatus == 2:
            return Response({"status": -1, "msg": "操作无效,流程异常了", "data": []})
        if not (c_p_ins.currentProcessNode.id == c_t_obj.tDefinitionId.id):
            c_p_ins.currentProcessNode = c_t_obj.tDefinitionId
            c_p_ins.save()
            return Response({"status": -1, "msg": "节点信息错误,节点位置已经更新", "data": []})
        if c_t_obj.taskStatus == 3:  # 当前任务执行异常
            c_p_ins.processStatus = 2
            c_p_ins.save()
            return Response({"status": -1, "msg": "当前节点异常", "data": []})
        # 正常情况
        if c_t_obj.taskStatus == 1 and c_p_ins.processStatus == 0:
            c_t_obj.taskStatus = 3  # 执行失败
            c_p_ins.processStatus = 2  # 流程异常
            c_t_obj.save()
            c_p_ins.save()
            b_models.WorkflowLog.objects.create(
                pInstance_number=c_p_ins.instance_name,
                suggestion=business_submit_advice,
                participant=str_user,
                taskInstanceId=c_t_obj.id,
                intervene_type_id=1,
                business_data=business_data_dict,
                business_map_relation=map_relation_dict,
                creator=c_p_ins.startUserID,
                business_blue_info=blue_print_info_dict
            )
            task_ins_dict = model_to_dict(c_t_obj)
            data = {}
            data["process_info"] = {'process_instance_number': c_p_ins.instance_name,
                                    'first_task_instance': task_ins_dict,
                                    'task_definition_id': c_t_obj.tDefinitionId.id}
            data["business_data"] = business_data_dict
            data["map_relation"] = map_relation_dict
            data["blue_print_info"] = blue_print_info_dict
            msg = u"该节点执行异常了,流程已标记异常,请重新处理"
            return Response({"status": 1, "msg": msg, "data": data})
        else:
            return Response({"status": -1, "msg": "流程状态异常,请具体检查错误", "data": []})

    @action(detail=False, methods=['post'], url_path='enter-my-approve-page')
    def enter_my_approve_page(self, request, *args, **kwargs):
        """
        进入我的审批页面
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        req_data = request.data
        process_definition_id = req_data.get("process_definition_id")
        task_definition_id = req_data.get("task_definition_id")
        process_instance_number = req_data.get("process_instance_number")
        process_instance_ins = models.ProcessInstance.objects.filter(instance_name=process_instance_number).first()
        if not process_instance_ins:
            return Response({"status": -1, "msg": "错误,没有当前对象~", "data": []})
        map_ins = ServerMapWf.objects.filter(work_flow_key=process_definition_id, node_id=task_definition_id).first()

        if not map_ins:
            return Response({"status": -1, "msg": "错误,没有当前对象~", "data": []})
        task_definition_ins = models.TaskDefinition.objects.filter(id=task_definition_id).first()
        task_ins = TaskInstance.objects.filter(pInstanceId=process_instance_ins,
                                               tDefinitionId=task_definition_ins).first()
        if not task_ins:
            # msg = msg_prefix + "失败，无此对象"
            return Response({"status": -1, "msg": "失败，无此对象", "data": []})
        business_log_ins = b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_number,
                                                               participant=None, taskInstanceId=task_ins).first()
        if not business_log_ins:
            return Response({"status": -1, "msg": "错误,没有当前对象~", "data": []})
        data = {}
        process_instance_data = model_to_dict(process_instance_ins)
        map_ins_data = model_to_dict(map_ins)
        data['map_relation'] = map_ins_data
        data['process_instance_info'] = process_instance_data
        data['business_data'] = business_log_ins.business_data

        return Response({"status": 1, "msg": "成功~", "data": data})


class BusinessToProcessModelView(ModelViewSet):
    """
    业务和流程的关系映射表的操作
    """
    queryset = models.BusinessToProcess.objects.all()
    # queryset1 = BlueInstance.objects.all()
    # print(queryset1)

    serializer_class = serializers.BusinessToProcessSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        for i in queryset:
            print(i.tables)

        # print table
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def look_look_process_detail(request, pk, *args, **kwargs):
    """
    查看流程的细节
    :param request:
    :return:
    """
    # username = request.META.get("HTTP_USERNAME")
    MSG = u"流程实例获取成功"
    if not pk:
        return HttpResponse("参数不全请重新输入")
    current_process_instance_obj = models.ProcessInstance.objects.filter(pk=pk).first()  # 流程实例
    p_id = current_process_instance_obj.id  # 实例id

    pdefintion_obj = current_process_instance_obj.pDefinitionId  # 实例对应的流程定义的id
    category_name = pdefintion_obj.pCategoryKey.processCategoryName
    p_node_count = pdefintion_obj.processNodes  # 流程定义的节点熟料
    definiton_name = pdefintion_obj.processDefinitionName  # 流程定义的名字
    pdefintion_queryset = models.ProcessInstance.objects.all()  # 流程定义
    if current_process_instance_obj.processStatus == 1:
        data1 = {
            # "node_name":node_name,
            "c_task_name": "暂无当前任务",
            "p_node_count": p_node_count,
            "definiton_name": definiton_name,
            "status_node": "任务执行完成",
        }
        from django.forms.models import model_to_dict
        p_obj = models.ProcessInstance.objects.get(pk=pk)

        data = model_to_dict(p_obj)
        data.update(data1)

        return Response({"status": 0, "msg": MSG, "data": data})
    else:
        current_definition_obj = TaskInstance.objects.filter(pInstanceId=current_process_instance_obj,
                                                             taskStatus=1).first()
        task_definition_obj = models.TaskDefinition.objects.filter(pDefinitionId=pdefintion_obj).first()
        task_ins_obj = TaskInstance.objects.filter(tDefinitionId=task_definition_obj).first()
        # current_node_status = task_ins_obj.taskStatus  # 当前节点状态
        # current_node_status = task_ins_obj.  # 当前节点状态
        # task_definition_obj1 = models.TaskDefinition.objects.filter(pDefinitionId=pdefintion_obj).all()
        candidate_set = current_definition_obj.tDefinitionId.candidate.all()  # 通过外键操作多对多对象

        l1 = []

        for i in candidate_set:
            dict2 = {}

            dict2["id"] = str(i.id)
            dict2["name"] = i.name

            l1.append(dict2)
        data1 = {
            # "node_name":node_name,
            "category_name": category_name,
            "c_task_name": current_definition_obj.taskName,
            "p_node_count": p_node_count,
            "definiton_name": definiton_name,
            # "status_node": current_definition_obj.taskStatus,
            "candidate": l1
        }
        from django.forms.models import model_to_dict
        p_obj = models.ProcessInstance.objects.get(pk=pk)

        data = model_to_dict(p_obj)
        data.update(data1)

        return Response({"status": 0, "msg": MSG, "data": data})


@api_view(["GET"])
def node_step_show(request, pk, *args, **kwargs):
    """
    当前实例的节点信息展示
    :param request:
    :param pk:
    :param args:
    :param kwargs:
    :return:
    """
    p_obj = models.ProcessInstance.objects.filter(pk=pk).first()

    all_node_set = TaskInstance.objects.filter(pInstanceId=p_obj).all()

    l1 = []

    for i in all_node_set:
        dict2 = {}
        print i.tDefinitionId.taskName
        dict2["id"] = str(i.id)
        dict2["taskName"] = i.taskName
        # dict2["taskNode"] = i.taskNode.taskName
        dict2["startTime"] = i.startTime
        dict2["endTime"] = i.endTime
        dict2["taskStatus"] = i.taskStatus

        l1.append(dict2)

    return Response({"status": 1, "msg": "操作成功", "data": l1})
