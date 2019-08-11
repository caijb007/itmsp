# coding: utf-8
# Author: Chery huo
import  time
from traceback import format_exc
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.forms.models import model_to_dict
from .serializers import *
from .models import *
from itmsp.utils.base import logger, smart_get
import datetime
from itmsp.utils.decorators import post_validated_fields, status, post_data_to_dict
from iuser.permissions import *
# from rest_framework.viewsets import ModelViewSet
# from rest_framework.decorators import action
from iuser.models import ExUser
from rest_framework.settings import api_settings

class VMGenerateApprovalViewSet(ModelViewSet):
    """
    申请表操作
    """
    queryset = VMGenerateApproval.objects.all()
    serializer_class = VMGenerateApprovalSerializer

    # @action(detail=False, methods=['post'], url_path='approval-test')
    def create(self, request, *args, **kwargs):
        msg_prefix = u"创建申请工单"
        """
        Create a model instance.
        """
        req_dict = post_data_to_dict(request.data)
        # req_dict = request.data
        business_data_dict = req_dict.get("business_data")
        map_relation_dict = req_dict.get("map_relation")

        process_info_dict = req_dict.get("process_info")
        if not process_info_dict:
            return Response({"status": -1, "msg": "没有流程数据", "data": []})
        # process_ins_info_dict = process_info_dict.get("process_ins_info")
        process_instance_number = process_info_dict.get("process_instance_number")
        if not process_instance_number:
            return Response({"status": -1, "msg": "没有流程实例编号", "data": []})
         # = business_data_dict.get("host_profile")instance_name
        submit_data_dict = business_data_dict.get("submit_data")
        submit_info_dict = submit_data_dict.get("submit_info")


        host_profile_list = submit_data_dict.get("host_config_data")
        apply_msg = submit_info_dict.get("submit_msg")
        # apply_expiration = req_dict.get("apply_expiration")
        is_haven_ins = VMGenerateApproval.objects.filter(workflow_number=process_instance_number).first()
        # 删除已存在的对象
        if is_haven_ins:
            set1 = is_haven_ins.vm_generate_ord.all()
            if set1:
                for i in set1:
                    i.delete()
            VMGenerateApproval.objects.filter(workflow_number=process_instance_number).delete()

        apply_application_list = submit_info_dict.get("submit_application")
        # print apply_application_list
        apply_expiration_str = smart_get(submit_info_dict, 'submit_expiration', str)
        print "dsadasd"
        print apply_expiration_str
        print "dsadasd"
        # '先创建申请表数据'
        now_time = time.strftime("%Y%m%d", time.localtime())  # 年月日
        instance_set = VMGenerateApproval.objects.all()
        instance_len = len(instance_set)
        i = 1
        i += instance_len
        k = "%03d" % i
        format_number = "approval" + now_time + k
        approval_user = request.user
        data= {}
        ins = VMGenerateApproval.objects.create(
            approval_number = format_number,
            applicant = approval_user,
            apply_msg = apply_msg,
            workflow_number = process_instance_number,
            map_relation = map_relation_dict
        )
        if not ins:
            return Response({"status": -1, "msg": "创建失败", "data": []})

        data['approval_ord'] = model_to_dict(ins)
        # '循环创建申请数据'
        # print len(host_profile_list)
        for i  in host_profile_list:
            # 'i 为每个 主机配置信息  字典格式'
            if not i:
                return Response({"status": -1, "msg": "申请数据创建失败", "data": []})
            env_type = i.get("env_type")
            apply_deploy_place = i.get("deploy_location")
            apply_os_version = i.get("apply_os_version")
            apply_node_type = i.get("node_type")
            apply_application_dict = apply_application_list
            apply_cpu = i.get("target_cpu_cores")
            apply_memory_gb = i.get("target_mem_gb")
            apply_software_dict = i.get("apply_software")
            apply_disk_gb = i.get("add_datadisk_gb")
            apply_network_area = i.get("network_area")
            # apply_expiration = i.get("apply_disk_gb")
            apply_system_dict = i.get("system_type")
            apply_filesystem_dict = i.get("apply_filesystem")
            ord_ins = VMGenerateApprovalOrd.objects.create(
                approval=ins,
                env_type =env_type,
                apply_os_version =apply_os_version,
                apply_deploy_place =apply_deploy_place,
                apply_node_type =apply_node_type,
                apply_application =apply_application_dict,
                apply_network_area =apply_network_area,
                apply_cpu =apply_cpu,
                apply_memory_gb =apply_memory_gb,
                apply_software =apply_software_dict,
                apply_disk_gb =apply_disk_gb,
                apply_system =apply_system_dict,
                apply_filesystem =apply_filesystem_dict,
                apply_expiration=apply_expiration_str
            )
            if not ord_ins:
                self.get_queryset().filter(id=ins.id).delete()
                return Response({"status": -1, "msg": "数据创建失败,申请删除", "data": []})
            # ord_ins.apply_expiration = apply_expiration_str
            # ord_ins.save()
        data['approval_data'] = model_to_dict(ord_ins)
        return Response({"status": 1, "msg": "创建申请数据成功", "data": data})

    @action(detail=False, methods=['post'], url_path='revocation-approval')
    def revocation_approval(self, request):
        """
        my process
        :param request:
        :return:
        """

        msg_prefix = u'撤销申请'

        # user = request.user
        req_data = request.data

        process_instance_number = req_data.get("process_instance_number")

        try:
            p_ins = VMGenerateApproval.objects.filter(workflow_number=process_instance_number).first()
            if not p_ins:
                return Response({"status": -1, "msg": "错误,当前申请对象不存在", "data": []})
            # t_ins_obj = TaskInstance.objects.filter(pInstanceId=p_ins, tDefinitionId=process_definition_id).first()

            # if not t_ins_obj:
            #     return Response({"status": -1, "msg": "错误,当前映射对象不存在", "data": []})
            p_data = model_to_dict(p_ins)
            # if t_ins_obj.taskStatus != 0:
            #     return Response({"status": -1, "msg": "错误,当前流程已提交，不可撤销", "data": []})
            # elif t_ins_obj.taskStatus == 0:
                # b_models.WorkflowLog.objects.filter(pInstance_number=process_instance_number).delete()
            approvalord_instance_queryset = VMGenerateApprovalOrd.objects.filter(approval=p_ins).order_by(
                'id').all()
            for i in approvalord_instance_queryset:
                i.delete()
            death_ins = VMGenerateApproval.objects.filter(workflow_number=process_instance_number).delete()
            data = {}
            if death_ins:
                data['approval_number'] = p_data.get('approval_number')
                return Response({"status": 1, "msg": "当前申请已被删除", "data": data})

            elif not p_ins:
                return Response({"status": -1, "msg": "当前申请未被删除", "data": []})
        except Exception, e:
            msg = msg_prefix + u"失败， 错误信息如下:" + unicode(e)
            return Response({"status": -1, "msg": msg, "data": []})
class VMGenerateApprovalOrderViewSet(ModelViewSet):
    """
    申请表数据
    """
    queryset = VMGenerateApprovalOrd.objects.all()
    serializer_class = VMGenerateApprovalOrderSerializer
import json
class VMGenerateApproveViewSet(ModelViewSet):
    """
    审批表操作
    """
    queryset = VMGenerateApprove.objects.all()
    serializer_class = VMGenerateApproveSerializer
    def create(self, request, *args, **kwargs):
        """
        创建审批数据用的
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = u"创建审批数据"
        approve_user = request.user

        req_dict = post_data_to_dict(request.data)
        # print "!" * 120
        # print req_dict
        # print "!" * 120
        business_data_dict = req_dict.get("business_data")
        process_info_dict = req_dict.get("process_info")
        blue_print_info_dict = req_dict.get("blue_print_info")
        print process_info_dict
        if not business_data_dict:
            return Response({"status":-1, "mag":"错误，无业务信息", 'data':[]})
        if not process_info_dict:
            return Response({"status":-1, "mag":"错误，无流程信息", 'data':[]})
        approve_data_dict = business_data_dict.get("submit_data")
        approve_result_list = business_data_dict.get("submit_result")
        if not approve_data_dict:
            return Response({"status":-1, "mag":"错误，无审批信息", 'data':[]})
        # if not approve_result_list:
        #     return Response({"status":-1, "mag":"错误，无审批配置信息", 'data':[]})
        approve_info_dict = approve_data_dict.get("submit_info")
        host_config_data_list = approve_data_dict.get("host_config_data")
        if not approve_info_dict:
            return Response({"status":-1, "mag":"错误，无审批基本信息", 'data':[]})
        if not host_config_data_list:
            return Response({"status":-1, "mag":"错误，无审批配置信息", 'data':[]})
        approve_msg = approve_info_dict.get("submit_advice") # 审批意见
        # process_ins_dict = process_info_dict.get("process_ins_info")
        process_task_ins_dict = process_info_dict.get("first_task_instance")
        # if not process_ins_dict:
        #     return Response({"status":-1, "mag":"错误，无流程实例信息", 'data':[]})
        # if not process_task_ins_dict:
        #     return Response({"status":-1, "mag":"错误，无任务实例信息", 'data':[]})
        process_ins_number = process_info_dict.get("process_instance_number")
        # print process_ins_number

        process_task_ins_id = process_task_ins_dict.get("id")





        approval_ins = VMGenerateApproval.objects.filter(workflow_number=process_ins_number).first()
        if not approval_ins:
            return Response({"status":-1, "mag":"错误，并无申请记录", 'data':[]})
        approval_ins_number = approval_ins.approval_number
        # '先创建申请表数据'
        now_time = time.strftime("%Y%m%d", time.localtime())  # 年月日
        instance_set = VMGenerateApprove.objects.all()
        instance_len = len(instance_set)
        i = 1
        i += instance_len
        k = "%03d" % i
        # l1 = str(time.time())
        # format_number = "approve" + now_time+l1[-2:] + k
        format_number = "approve" + now_time + k

        blue_instance_number = blue_print_info_dict.get("blue_instance_number")
        blue_status = blue_print_info_dict.get("blue_status")
        # blue_print_info_dict.get("blue_status")
        status_number = ''
        if blue_status ==3: # 异常
            status_number = blue_status
        elif blue_status==2: # 完成
            status_number = blue_status
        # approve_number = approve_info_dict.get("approve_number")
        approve_ord_id = approve_info_dict.get("approve_ord_id")
        # if approve_number:# 如果是已经存在的审批单
        # old_approve_ins = VMGenerateApprove.objects.filter(approve_number=approve_number).first()

        approve_ord_ins = VMGenerateApproveOrd.objects.filter(id=approve_ord_id).first()
        # print "%" *20
        # print approve_ord_ins
        # print "%" *20
        old_approve_ins = approve_ord_ins.approve
        if old_approve_ins and approve_ord_ins:
            # print "dasdasdasdasdasd"
            old_approve_ins.status = status_number
            old_approve_ins.approve_result = approve_result_list
            old_approve_ins.save()
            # approve_ord_ins = VMGenerateApprovalOrd.objects.filter(id=approve_ord_id).first()
            host_config_data_dict = host_config_data_list[0]
            appro_expiration_str = smart_get(approve_info_dict, 'submit_expiration', str)
            appro_application_list = approve_info_dict.get("submit_application")
            env_type = host_config_data_dict.get("env_type")
            appro_deploy_place = host_config_data_dict.get("deploy_location")
            appro_os_version = host_config_data_dict.get("os_version")
            appro_node_type = host_config_data_dict.get("node_type")
            appro_network_area_str = host_config_data_dict.get("network_area")
            appro_cpu = host_config_data_dict.get("target_cpu_cores")
            appro_memory_gb = host_config_data_dict.get("target_mem_gb")
            # appro_software_list = i.get("software",{})
            appro_disk_gb = host_config_data_dict.get("add_datadisk_gb")
            appro_system_dict = host_config_data_dict.get("system_type")
            appro_filesystem_dict = host_config_data_dict.get("apply_filesystem")


            # approve_ord_ins.approve=old_approve_ins
            approve_ord_ins.env_type=env_type
            approve_ord_ins.deploy_location=appro_deploy_place
            approve_ord_ins.appro_os_version=appro_os_version
            approve_ord_ins.node_type=appro_node_type
            approve_ord_ins.application=appro_application_list
            #approve_ord_ins.appro_software=appro_software_list,
            approve_ord_ins.network_area=appro_network_area_str
            approve_ord_ins.target_cpu_cores=appro_cpu
            approve_ord_ins.target_mem_gb=appro_memory_gb
            approve_ord_ins.add_datadisk_gb=appro_disk_gb
            approve_ord_ins.expiration=appro_expiration_str
            approve_ord_ins.system_type=appro_system_dict
            approve_ord_ins.apply_filesystem=appro_filesystem_dict
            approve_ord_ins.configuration_resource_information=host_config_data_dict
            approve_ord_ins.save()


            if not approve_ord_ins:
                is_delete = VMGenerateApprove.objects.filter(approve_number=approve_ord_ins.approval.approve_number).delete()
                if is_delete:
                    return Response({"status": -1, "msg": "审批数据创建失败，审批工单已删除", "data": []})
            data = model_to_dict(approve_ord_ins)

            return Response({"status": 1, "msg":"重新创建审批数据成功", "data": data})

        else:
            approve_ins = VMGenerateApprove.objects.create(
                approval_number =approval_ins_number,
                approve_number = format_number,
                workflow_number = process_ins_number,
                workflow_note_ins_id=process_task_ins_id,
                status=status_number,
                aprover = approve_user,
                approve_msg=approve_msg,
                approve_result=approve_result_list,
                blue_ins_number=blue_instance_number

            )
            if not approve_ins:
                return Response({"status": -1, "mag": "错误，无法创建审批信息", 'data': []})

            # '循环创建审批数据'
            # print len(host_profile_list)
            appro_expiration_str = smart_get(approve_info_dict, 'submit_expiration', str)
            appro_application_list = approve_info_dict.get("submit_application")
            list1 = []
            for i  in host_config_data_list:
                # 'i 为每个 主机配置信息  字典格式'
                if not i:
                    return Response({"status": -1, "msg": "审批工单创建失败", "data": []})
                env_type = i.get("env_type")
                appro_deploy_place = i.get("deploy_location")
                appro_os_version = i.get("os_version")
                appro_node_type = i.get("node_type")
                appro_network_area_str = i.get("network_area")
                appro_cpu = i.get("target_cpu_cores")
                appro_memory_gb = i.get("target_mem_gb")
                # appro_software_list = i.get("software",{})
                appro_disk_gb = i.get("add_datadisk_gb")
                appro_system_dict = i.get("system_type")
                appro_filesystem_dict = dict(i.get("apply_filesystem"))
                print appro_filesystem_dict
                # print type(appro_application_list)
                # print type(i)

                approve_ord_ins = VMGenerateApproveOrd.objects.create(
                    approve=approve_ins,
                    env_type=env_type,
                    deploy_location=appro_deploy_place,
                    appro_os_version=appro_os_version,
                    node_type=appro_node_type,
                    application=appro_application_list,
                    # appro_software=appro_software_list,
                    network_area=appro_network_area_str,
                    target_cpu_cores=appro_cpu,
                    target_mem_gb=appro_memory_gb,
                    add_datadisk_gb=appro_disk_gb,
                    expiration=appro_expiration_str,
                    system_type=appro_system_dict,
                    apply_filesystem=appro_filesystem_dict,
                    configuration_resource_information=i,
                )
                if not approve_ord_ins:
                    is_delete = VMGenerateApprove.objects.filter(approve_number=approve_ins.approve_number).delete()
                    if is_delete:
                        return Response({"status": -1, "msg": "审批数据创建失败，审批工单已删除", "data": []})
                data = model_to_dict(approve_ord_ins)
                list1.append(data)
            if not list1:
                return Response({"status": -1, "msg": "审批数据查看失败", "data": []})
            return Response({"status": 1, "msg": "创建审批数据成功", "data": list1})




class VMGenerateApproveOrderViewSet(ModelViewSet):
    """
    审批数据表操作
    """
    queryset = VMGenerateApproveOrd.objects.all()
    serializer_class = VMGenerateApproveOrdSerializer

    @action(detail=False, methods=['post'], url_path='get-all-approve-list')
    def get_all_approve_list(self, request, *args, **kwargs):
        """
        获取审批详情中的业务数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = "获取审批详情中的业务数据"
        process_instance_dict = request.data.get("process_info")
        # business_data_dict = request.data.get("business_data")
        # map_relation_dict = request.data.get("map_relation")
        try:
            if not process_instance_dict:
                raise Exception("没有流程信息")
            # if not business_data_dict:
            #     raise Exception("没有业务信息")
            process_instance_number = process_instance_dict.get("process_instance_number")
            # task_definition_id = process_instance_dict.get("task_definition_id")
            VMGenerateApprove_ins_set = VMGenerateApprove.objects.filter(workflow_number=process_instance_number).all()

            print VMGenerateApprove_ins_set
            list1 = []
            for i in VMGenerateApprove_ins_set:
                approve_ord_ins = i.vm_generate_approve_ord.first()


                serializer = self.get_serializer(approve_ord_ins)
                # serializer = VMGenerateApproveOrdSerializer(instance=approve_ord_ins)
                list1.append(serializer.data)
            # return Response(serializer.data)
        except Exception as e:
            msg = msg_prefix + " 失败， 错误信息:" + unicode(e)
            return Response({"status": -1, "msg": msg, "data": []})
        else:
            msg = "成功"

            return Response({"status": 1, "msg": msg, "data": list1})
            # return Response({"status": 1, "msg": msg, "data": ssss})