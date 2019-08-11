# coding: utf-8
# Author: Chery huo


from multiprocessing import Process
import json
import requests
from datetime import datetime
from iconfig.models import BlueEngineTask
from rest_framework.decorators import api_view
from rest_framework.response import Response
from itmsp.settings import LOCAL_HOST, LOCAL_PORT
from itmsp.utils.decorators import post_data_to_dict
from iservermenu.models import Button
from iservermenu.blueprint_to_workflow.tools import return_dict_value

import time


@api_view(['POST'])
def bwmq_api(request):
    """
    用来接收请求和循环调用蓝图和流程等接口
    :param request:
    :return:
    """

    ##########################新代码##################################################
    # PORT = "8030"
    PORT = LOCAL_PORT
    # print PORT
    blue_relative_url = "/iconfig/blue-engine-query/"
    process_agree_relative_url = "/iworkflow/taskinstance/agree_interface/"
    process_over_relative_url = "/iworkflow/pinstance/process_over/"

    process_ins_error_relative_url = "/iworkflow/taskinstance/process-ins-error/"
    # req_data = post_data_to_dict(request.data)

    authorization = request.META.get('HTTP_AUTHORIZATION')  # token 76e25c7f4265592a44f258261180a175f20912d4
    headers = {'content-type': 'application/json', "authorization": authorization}
    base_url = "http://" + LOCAL_HOST + ":" + PORT
    blue_url = "http://" + LOCAL_HOST + ":" + PORT + blue_relative_url
    process_agree_url = "http://" + LOCAL_HOST + ":" + PORT + process_agree_relative_url
    process_over_url = "http://" + LOCAL_HOST + ":" + PORT + process_over_relative_url
    process_ins_error_url = "http://" + LOCAL_HOST + ":" + PORT + process_ins_error_relative_url
    ori_data = post_data_to_dict(request.data)
    req_data = format_request(data=ori_data)

    if req_data['status'] == -1:
        return Response({"status": -1, "msg": "格式化数据函数执行失败", "data": []})


    elif req_data['status'] == 1:
        every_blue_print_list = req_data.get('data')
        fin_list = []
        for data in every_blue_print_list:  # 循环每一个源格式的请求对象
            # 调用蓝图的接口

            time.sleep(0.3)  # 太快会报错
            blue_func_req = transfer_bp(url=blue_url, headers=headers, req_data=data)
            print  "!" * 100
            print  blue_func_req
            print  "!" * 100
            if blue_func_req['status'] == -1:  # 函数调用失败
                return Response({"status": -1, "msg": "调用蓝图的接口失败", 'data': []})
            elif blue_func_req['status'] == 1:
                ret_data = blue_func_req['data']
                if not ret_data:
                    return Response({"status": -1, "msg": "调用蓝图的接口返回值为空", 'data': []})
                blue_print_info_dict = ret_data.get('blue_print_info')
                print "循环查询蓝图状态之前:", blue_print_info_dict
                while blue_print_info_dict['blue_status'] == 1:

                    print "蓝图sss正在执行中"
                    blue_func_req = transfer_bp(url=blue_url, headers=headers, req_data=data)
                    print "循环查询蓝图状态内容:", blue_func_req
                    time.sleep(3)  # 3秒发送
                    ret_data = blue_func_req['data']  # 源数据
                    if not ret_data:
                        return Response({"status": -1, "msg": "调用蓝图的接口返回值为空", 'data': []})
                    blue_print_info_dict = ret_data.get('blue_print_info')

                if blue_print_info_dict['blue_status'] == 3:  # 调用流程异常的接口

                    # 异常的话先调用业务数据接口
                    finish_req = data_analysis_and_data_write_back(req_data=ret_data, base_url=base_url,
                                                                   headers=headers)
                    if finish_req['status'] == -1:
                        finish_ret = finish_req['data']
                        return Response({"status": -1, "msg": "调用业务数据回写接口返回值为失败", 'data': finish_ret})
                    if finish_req['status'] == 1:
                        finish_ret = finish_req['data']
                        fin_list.append(ret_data)

                elif blue_print_info_dict['blue_status'] == 2:  # 蓝图状态已经完成了
                    # time.sleep(1)  # 太快会报错
                    business_info_dict = ret_data.get('business_data')  # 业务数据字典
                    if not business_info_dict:
                        return Response({"status": -1, "msg": "业务数据回写失败,调用失败", 'data': []})
                    business_info_dict['submit_result'] = blue_print_info_dict.get('result_data')
                    ret_data['business_data'] = business_info_dict  # 重写 业务数据

                    finish_req = data_analysis_and_data_write_back(req_data=ret_data, base_url=base_url,
                                                                   headers=headers)
                    if finish_req['status'] == -1:
                        finish_ret = finish_req['data']
                        return Response({"status": -1, "msg": "调用业务数据回写接口返回值为失败", 'data': finish_ret})
                    if finish_req['status'] == 1:
                        fin_list.append(ret_data)

        is_ok_status_list = []
        submit_result_list1 = []  # 多个蓝图结果的返回的列表，只有成功的
        # 获取部分原始请求信息和返回结果进行重新结构组合
        old_process_info_dict = request.data.get("process_info")
        old_map_relation_dict = request.data.get("map_relation")
        old_business_data_dict = request.data.get("business_data")
        old_blue_print_info_list = request.data.get("blue_print_info")
        # old_submit_data_dict = old_business_data_dict.get("submit_data")

        for i in fin_list:
            blue_print_info_dict = i.get('blue_print_info')
            blue_status = blue_print_info_dict.get('blue_status')
            is_ok_status_list.append(blue_status)
            #############将数据重新打包成调度中心调度之前的结构，重新传给流程
            business_data_dict = i.get('business_data')
            submit_result_list = business_data_dict.get('submit_result')
            for submit_result in submit_result_list:
                submit_result_list1.append(submit_result)

        # 蓝图执行后的结果重写到原来的位置
        old_business_data_dict["submit_result"] = submit_result_list1

        net_refactoring_dict = {}
        net_refactoring_dict["process_info"] = old_process_info_dict
        net_refactoring_dict["map_relation"] = old_map_relation_dict
        net_refactoring_dict["business_data"] = old_business_data_dict
        net_refactoring_dict["blue_print_info"] = old_blue_print_info_list

        set1 = set(is_ok_status_list)
        set0 = {2}
        print "打印出蓝图状态列表:", set1
        #
        if set1 != set0:  # 有异常的蓝图
            print "调用流程异常的接口"
            # blue_print_info_dict=req_data['blue_print_info']
            process_error_func_req = transfer_workflow_error_process(url=process_ins_error_url, headers=headers,
                                                                     req_data=net_refactoring_dict)
            if process_error_func_req['status'] == -1:
                return Response({"status": -1, "msg": "调用流程异常接口返回值为失败", 'data': process_error_func_req})
            elif process_error_func_req['status'] == 1:  # 同意成功就可以结束进程了
                return Response({"status": 1, "msg": "调用流程异常接口返回值为成功", 'data': process_error_func_req['data']})
            # return Response({"status": 1, "msg": "调用业务数据回写接口返回值为成功", 'data': finish_ret})
        else:  # 都是完成的蓝图
            print "调用流程同意的接口"
            process_func_req = transfer_workflow_agree(url=process_agree_url, headers=headers,
                                                       req_data=net_refactoring_dict)
            if process_func_req['status'] == -1:
                return Response({"status": -1, "msg": "调用流程同意接口返回值为失败", 'data': []})
            elif process_func_req['status'] == 1:  # 同意成功就可以结束进程了
                req_data = process_func_req['data']

                process_ins_over_req = transfer_workflow_over_process(url=process_over_url, headers=headers,
                                                                      req_data=req_data)
                if process_ins_over_req['status'] == -1:
                    return Response({"status": -1, "msg": "调用流程结束接口返回值为失败", 'data': []})
                elif process_ins_over_req['status'] == 1:  # 结束接口返回值成功
                    return Response({"status": 1, "msg": "调用流程结束接口返回值为成功", 'data': process_ins_over_req})

        return Response({"status": 1, "msg": "格式化数据函数执行成功", "data": net_refactoring_dict})


@api_view(['POST'])
def restart_bw_mq(request):
    """
    用于重启流程和蓝图
    :param request:
    :return:
    """
    # req_data = request.data

    # 调用查询蓝图

    PORT = "8030"
    # PORT = LOCAL_PORT
    blue_relative_url = "/iconfig/blue-engine-query/"
    process_agree_relative_url = "/iworkflow/taskinstance/agree_interface/"
    process_over_relative_url = "/iworkflow/pinstance/process_over/"

    process_ins_error_relative_url = "/iworkflow/taskinstance/process-ins-error/"
    # req_data = post_data_to_dict(request.data)

    authorization = request.META.get('HTTP_AUTHORIZATION')  # token 76e25c7f4265592a44f258261180a175f20912d4
    headers = {'content-type': 'application/json', "authorization": authorization}
    base_url = "http://" + LOCAL_HOST + ":" + PORT
    blue_url = "http://" + LOCAL_HOST + ":" + PORT + blue_relative_url
    process_agree_url = "http://" + LOCAL_HOST + ":" + PORT + process_agree_relative_url
    process_over_url = "http://" + LOCAL_HOST + ":" + PORT + process_over_relative_url
    process_ins_error_url = "http://" + LOCAL_HOST + ":" + PORT + process_ins_error_relative_url
    ori_data = post_data_to_dict(request.data)
    # req_data = format_request(data=ori_data)
    blue_func_req = transfer_bp(url=blue_url, headers=headers, req_data=ori_data)
    # print  "!" * 100
    # print  blue_func_req
    # print  "!" * 100
    if blue_func_req['status'] == -1:  # 函数调用失败
        return Response({"status": -1, "msg": "调用蓝图的接口失败", 'data': []})
    elif blue_func_req['status'] == 1:
        ret_data = blue_func_req['data']
        if not ret_data:
            return Response({"status": -1, "msg": "调用蓝图的接口返回值为空", 'data': []})
        blue_print_info_dict = ret_data.get('blue_print_info')
        while blue_print_info_dict['blue_status'] == 1:
            print "蓝图sss正在执行中"
            # 修改流程状态
            process_req = edit_process_status(ori_data,0)
            if process_req['status'] == -1:
                return Response({"status": -1, "msg": "调用流程修改状态的操作失败", 'data': []})
            # 再次检测
            blue_func_req = transfer_bp(url=blue_url, headers=headers, req_data=ori_data)
            time.sleep(5)  # 5秒发送
            ret_data = blue_func_req['data']  # 源数据
            if not ret_data:
                return Response({"status": -1, "msg": "调用蓝图的接口返回值为空", 'data': []})

            blue_print_info_dict = ret_data.get('blue_print_info')

        if blue_print_info_dict['blue_status'] == 3:  # 调用流程异常的接口
            # 修改流程
            process_error_func_req = transfer_workflow_error_process(url=process_ins_error_url, headers=headers,
                                                                     req_data=ori_data)
            if process_error_func_req['status'] == -1:
                return Response({"status": -1, "msg": "调用流程异常接口返回值为失败", 'data': process_error_func_req})
            elif process_error_func_req['status'] == 1:  # 同意成功就可以结束进程了
                return Response({"status": 1, "msg": "调用流程异常接口返回值为成功", 'data': process_error_func_req['data']})

        elif blue_print_info_dict['blue_status'] == 2:  # 蓝图状态已经完成了

            business_info_dict = ret_data.get('business_data')  # 业务数据字典
            if not business_info_dict:
                return Response({"status": -1, "msg": "业务数据回写失败,调用失败", 'data': []})
            business_info_dict['submit_result'] = blue_print_info_dict.get('result_data')
            ori_data['business_data'] = business_info_dict  # 重写 业务数据
            finish_req = data_analysis_and_data_write_back(req_data=ori_data, base_url=base_url,
                                                           headers=headers)
            if finish_req['status'] == -1:
                finish_ret = finish_req['data']
                return Response({"status": -1, "msg": "调用业务数据回写接口返回值为失败", 'data': finish_ret})

            process_func_req = transfer_workflow_agree(url=process_agree_url, headers=headers, req_data=ori_data)
            # print process_func_req
            if process_func_req['status'] == -1:
                return Response({"status": -1, "msg": "调用流程同意接口返回值为失败", 'data': []})
            elif process_func_req['status'] == 1:  # 同意成功就可以结束进程了
                req_data = process_func_req['data']

                process_ins_over_req = transfer_workflow_over_process(url=process_over_url, headers=headers,
                                                                      req_data=req_data)
                if process_ins_over_req['status'] == -1:
                    return Response({"status": -1, "msg": "调用流程结束接口返回值为失败", 'data': []})
                elif process_ins_over_req['status'] == 1:  # 结束接口返回值成功

                    return Response({"status": 1, "msg": "重新调用流程结束接口返回成功", 'data': process_ins_over_req['data']})
            return Response({"status": 1, "msg": "蓝图状态已经完成了", 'data': ori_data})
        return Response({"status": 1, "msg": "蓝图状态正常", 'data': ori_data})
        # return Response({"status": 1, "msg": "dsad", "data": blue_print_info_dict})

    # return Response({"status": 1, "msg": "dsad", "data": ori_data})


def format_request(data):
    """
    用于格式化请求的数据，重新整个成一个标准的包包
    :param data:
    :return:
    """

    business_data_dict = data.get("business_data")
    map_relation_dict = data.get("map_relation")
    process_info_dict = data.get("process_info")
    blue_print_info_list = data.get("blue_print_info")
    if not business_data_dict:
        return Response({"status": -1, "msg": "business_data_dict", "data": []})
    big_list = []
    for i in blue_print_info_list:
        req_data = get_out_blue_data_and_format_data(data=i)

        if req_data['status'] == -1:
            return {"status": -1, "msg": "蓝图业务数据返回函数失败", "data": []}
        elif req_data['status'] == 1:
            business_data_dict = req_data['data']
            new_construction_dict = {}
            new_construction_dict['map_relation'] = map_relation_dict
            new_construction_dict['process_info'] = process_info_dict
            new_construction_dict['business_data'] = business_data_dict
            new_construction_dict['blue_print_info'] = i
            big_list.append(new_construction_dict)

    return {"status": 1, "msg": "blue_print_info_list", "data": big_list}


from iconfig.models import BlueAccessModuleParamsInstance


# from iconfig.serializers import BlueAccessModuleParamsInstanceSerializer
def get_out_blue_data_and_format_data(data):
    """
    根据蓝图信息返回蓝图对象信息
    :param data:
    :return:
    """

    """
     {
            "blue_instance_number": "blue201908060005"
    }
    """

    blue_instance_number = data.get("blue_instance_number")
    blue_log_ins = BlueAccessModuleParamsInstance.objects.filter(blue_instance_number=blue_instance_number).first()
    # serializer = BlueAccessModuleParamsInstanceSerializer(instance=blue_log_ins)

    data1 = blue_log_ins.business_data
    if not data1:
        return {"status": -1, "msg": "not blue_print_business_data", "data": []}
    return {"status": 1, "msg": "not blue_print_info_list", "data": data1}


def transfer_bp(url, headers, req_data):
    """
    调用蓝图的查询接口
    :param url:
    :param req_data:
    :return:
    """
    # print "*" * 100
    # print req_data, type(req_data)
    # print "*" * 100
    blue_print_info_dict = req_data.get("blue_print_info")
    # print "调用蓝图的查询接口", blue_print_info_dict

    blue_instance_number = blue_print_info_dict.get("blue_instance_number")
    # print blue_instance_number
    blue_instance_params_list = ["result_data", "blue_instance_number"]
    msg_prefix = u"调用蓝图的查询接口"
    # print u"调用蓝图的查询接口"
    try:
        data1 = {"blue_instance_number": blue_instance_number,
                 "blue_instance_params": blue_instance_params_list}  # 这就是一个str, 如果用赋值的方式就是一个列表,不知为何
        # print data1
        r = requests.post(url=url, headers=headers, data=json.dumps(data1))
        # print r.status_code
        if r.raise_for_status():
            return r.raise_for_status()

        if r.json():
            return_data = r.json()
            if return_data['status'] == -1:
                return {"status": -1, "msg": "调用失败", "data": return_data}
            elif return_data['status'] == 1:
                blue_print_dict = {
                    "blue_ins_number": blue_instance_number,
                    "blue_result": return_data['data']
                }
                # req_data['blue_print_info'] = blue_print_dict
                req_data['blue_print_info'] = return_data['data']
                # json_data = json.dumps(req_data)
                return {"status": 1, "msg": "调用成功", "data": req_data}

    except Exception, e:
        msg = msg_prefix + "失败，错误信息：" + unicode(e)
        return {"status": -1, "msg": msg, "data": []}


def transfer_workflow_agree(url, headers, req_data):
    """
    调用流程节点同意接口
    :param url:
    :param req_data:
    :return:
    """

    msg_prefix = "调用流程节点同意接口"

    # req_data = req_data)
    # print req_data

    # map_relation_dict = req_data.get("map_relation")  # 映射信息
    # if not map_relation_dict:
    #     msg = msg_prefix + u"失败，当前映射关系无效"
    #     return Response({"status": -1, "msg": msg, "data": []})
    try:
        r = requests.post(url=url, headers=headers, data=json.dumps(req_data))
        print r.json()
        if r.raise_for_status():
            return r.raise_for_status()

        if r.json():
            return_data = r.json()
            if return_data['status'] == -1:
                return {"status": -1, "msg": "流程同意接口操作失败", "data": return_data}
            elif return_data['status'] == 1:
                # blue_print_dict = {
                #     "blue_ins_number": blue_instance_number,
                #     "blue_result": return_data['data']
                # }
                # req_data['blue_print_info'] = blue_print_dict
                # req_data['blue_print_info'] = return_data['data']

                return {"status": 1, "msg": "流程同意接口操作成功", "data": return_data}
    except Exception, e:
        msg = msg_prefix + "失败，错误信息：" + unicode(e)
        return {"status": -1, "msg": msg, "data": []}

    # return {"status": 1, 'msg': 'Interface is Ok', 'data': []}


def transfer_workflow_refuse(url, headers, req_data):
    """
    调用流程节点拒绝接口
    :param url:
    :param req_data:
    :return:
    """
    # url = "http://118.240.13.50:8879/iconfig/blue-engine-query"
    # # req_req = requests.post()
    # headers = {'Connection': 'close', "authorization": request.META.get('HTTP_AUTHORIZATION')}
    #
    # data = {"blue_instance_number": blue_instance_number, "blue_instance_params": "result_data"}
    # req_req = requests.post(url, data=data, headers=headers)
    msg_prefix = "调用流程节点拒绝接口"
    try:
        req_data = req_data['data']
        r = requests.post(url=url, headers=headers, data=json.dumps(req_data))
        # print r.json()
        if r.raise_for_status():
            return r.raise_for_status()

        if r.json():
            return_data = r.json()
            if return_data['status'] == -1:
                return {"status": -1, "msg": "流程拒绝接口操作失败", "data": return_data}
            elif return_data['status'] == 1:
                # blue_print_dict = {
                #     "blue_ins_number": blue_instance_number,
                #     "blue_result": return_data['data']
                # }
                # req_data['blue_print_info'] = blue_print_dict
                # req_data['blue_print_info'] = return_data['data']

                return {"status": 1, "msg": "流程拒绝接口操作成功", "data": return_data}
    except Exception, e:
        msg = msg_prefix + "失败，错误信息：" + unicode(e)
        return {"status": -1, "msg": msg, "data": []}


def transfer_workflow_over_process(url, headers, req_data):
    """
    调用流程节点结束接口
    :param url:
    :param req_data:
    :return:
    """
    msg_prefix = "调用流程节点结束接口"
    try:
        req_data = req_data['data']
        r = requests.post(url=url, headers=headers, data=json.dumps(req_data))
        # print r.json()
        if r.raise_for_status():
            return r.raise_for_status()

        if r.json():
            return_data = r.json()
            if return_data['status'] == -1:
                return {"status": -1, "msg": "流程结束接口操作失败", "data": return_data}
            elif return_data['status'] == 1:
                # blue_print_dict = {
                #     "blue_ins_number": blue_instance_number,
                #     "blue_result": return_data['data']
                # }
                # req_data['blue_print_info'] = blue_print_dict
                # req_data['blue_print_info'] = return_data['data']

                return {"status": 1, "msg": "流程结束接口操作成功", "data": return_data}
    except Exception, e:
        msg = msg_prefix + "失败，错误信息：" + unicode(e)
        return {"status": -1, "msg": msg, "data": []}


def transfer_workflow_error_process(url, headers, req_data):
    """
    调用流程节点异常接口
    :param url:
    :param req_data:
    :return:
    """
    # url = "http://118.240.13.50:8879/iconfig/blue-engine-query"
    # # req_req = requests.post()
    # headers = {'Connection': 'close', "authorization": request.META.get('HTTP_AUTHORIZATION')}
    #
    # data = {"blue_instance_number": blue_instance_number, "blue_instance_params": "result_data"}
    # req_req = requests.post(url, data=data, headers=headers)
    msg_prefix = "调用流程异常接口"
    try:
        req_data = req_data
        # print req_data
        r = requests.post(url=url, headers=headers, data=json.dumps(req_data))
        #

        # print " 调用流程异常接口返回"
        # print r.json()
        # print " 调用流程异常接口返回"
        if r.raise_for_status():
            return r.raise_for_status()

        if r.json():
            return_data = r.json()
            if return_data['status'] == -1:
                return {"status": -1, "msg": "流程异常接口操作失败", "data": return_data}
            elif return_data['status'] == 1:
                # blue_print_dict = {
                #     "blue_ins_number": blue_instance_number,
                #     "blue_result": return_data['data']
                # }
                # req_data['blue_print_info'] = blue_print_dict
                # req_data['blue_print_info'] = return_data['data']

                return {"status": 1, "msg": "流程异常接口操作成功", "data": return_data}
    except Exception, e:
        msg = msg_prefix + "失败，错误信息：" + unicode(e)
        return {"status": -1, "msg": msg, "data": []}


def data_analysis_and_data_write_back(req_data, base_url, headers):
    req_data1 = req_data
    print "!" * 120
    print req_data
    print "!" * 120
    map_relation_dict = req_data.get("map_relation")
    msg_prefix = u"数据分析和数据回写"
    try:
        if not map_relation_dict:
            raise Exception("无映射关系信息")
        synthesize_code = map_relation_dict.get("synthesize_code")
        button_ins = Button.objects.filter(composite_code=synthesize_code).first()
        server_key = button_ins.page.server.description
        if not server_key:
            raise Exception("无服务表记录，无法回写数据")
        relative_url = return_dict_value(server_key)  # 拿到相对路径
        if not relative_url:
            raise Exception("查不到路径，无法回写数据")
        print relative_url
        com_url = base_url + relative_url
        if not relative_url:
            raise Exception("查不到url，无法回写数据")
        print com_url
        r = requests.post(url=com_url, headers=headers, data=json.dumps(req_data1))
        if r.raise_for_status():
            return r.raise_for_status()
        if r.json():
            return_data = r.json()
            if return_data['status'] == -1:
                return {"status": -1, "msg": "业务回写接口操作失败", "data": return_data}
            elif return_data['status'] == 1:
                # blue_print_dict = {
                #     "blue_ins_number": blue_instance_number,
                #     "blue_result": return_data['data']
                # }
                # req_data['blue_print_info'] = blue_print_dict
                # req_data['blue_print_info'] = return_data['data']

                return {"status": 1, "msg": "业务回写接口操作成功", "data": return_data}
    except Exception, e:
        msg = msg_prefix + "失败，错误信息：" + unicode(e)
        return {"status": -1, "msg": msg, "data": []}

from iworkflow.models import ProcessInstance
from django.forms.models import model_to_dict
def edit_process_status(data,number):
    process_info_dict = data.get("process_info")
    if not process_info_dict:
        return {"status": -1, "msg": "暂无流程数据", "data": []}
    process_instance_number = data.get("process_instance_number")
    if not process_instance_number:
        return {"status": -1, "msg": "无流程数据", "data": []}
    process_ins = ProcessInstance.objects.filter(instance_name=process_instance_number).first()
    if not process_ins:
        return {"status": -1, "msg": "无流程对象", "data": []}
    # if process_ins.processStatus == 0:
    #     return {"status": -1, "msg": "流程未异常，不可修改", "data": []}
    # elif process_ins.processStatus == 1:
    #     return {"status": -1, "msg": "流程已完成,不可修改", "data": []}
    # process_ins.processStatus  流程异常状态
    process_ins.processStatus =number #修改成目标状态
    process_ins.save()
    process_data = model_to_dict(process_ins)
    return {"status": 1, "msg": "流程状态已修改完成", "data": process_data}

# def update_business_data(data)
