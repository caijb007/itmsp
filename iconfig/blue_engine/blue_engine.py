# coding: utf-8
# Author: Chery Huo
from iconfig.models import *
from traceback import format_exc
from rest_framework.response import Response
from django.forms.models import model_to_dict
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from datetime import datetime
from itmsp.utils.base import logger
from iconfig.models import BlueEngineTask
from iconfig.blue_instance_api.blue_instance_api import BlueInstanceAPI
from itmsp.utils.base import set_log, smart_get, LOG_LEVEL
from itmsp.utils.decorators import post_data_to_dict
from iconfig.blue_engine.utils import set_log
from iconfig.blue_engine.blue_logger import blue_engine_task_logger, tail
from iconfig.tasks import blue_engine_control_center
import json
# from    celery.utils.in
list1 = []
blue_engine_logger = set_log(LOG_LEVEL)


class BLueEngine(APIView):
    """
    此类属于蓝图引擎类，用于提供蓝图实例化接口调用和任务的执行
    """
    globals_note_list = []

    @staticmethod
    @api_view(["POST"])
    # @auto_log
    def blue_engine_query(request):
        """
        此静态方法用于 蓝图引擎的查询接口，
        :param request: 接受查询参数
        :return:
        """
        msg_prefix = u"蓝图引擎任务接口查询"
        # print request.data
        blue_instance_number = request.data.get('blue_instance_number')
        print blue_instance_number, type(blue_instance_number)
        blue_instance_params_list = request.data.get('blue_instance_params')
        b_p_i_o = BlueEngineTask.objects.filter(blue_instance_number=blue_instance_number).first()
        if not b_p_i_o:
            return Response({"status": -1, "msg": "暂无当前蓝图实例记录", "data": []})
        req_dict = {}
        try:

            for i in blue_instance_params_list:

                # print b_ins
                if i != "blue_instance_status" and i not in b_p_i_o.__dict__.keys():
                    return Response({"status": -1, "msg": "蓝图引擎任务获取失败,传值错误", "data": []})
                str_l = "b_p_i_o.%s" % i
                req_dict[i] = eval(str_l)

            # print LOCAL_HOST,LOCAL_PORT

            if req_dict:

                b_ins = BlueInstance.objects.filter(blue_instance_number=blue_instance_number).first()
                if not b_ins:
                    msg = msg_prefix + u"失败,没有当前实例编号"
                    return Response({"status": -1, "msg": msg, "data": []})
                req_dict['blue_status'] = b_ins.status  # 赠送的蓝图返回值

                msg = msg_prefix + u"成功"
                return Response({"status": 1, "msg": msg, "data": req_dict})


        except Exception as e:
            if not b_p_i_o:
                msg = msg_prefix + u"失败,没有当前实例编号, 错误信息: " + unicode(e)
                return Response({"status": -1, "msg": msg, "data": []})
            if not blue_instance_params_list:
                msg = msg_prefix + u"失败,没有传入参数 错误信息: " + unicode(e)
                return Response({"status": -1, "msg": msg, "data": []})
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            blue_engine_task_logger.error(msg)
        else:
            msg = msg_prefix + u"成功"
            return Response({"status": 1, "msg": msg, "data": req_dict})

    @staticmethod
    @api_view(["POST"])
    def blue_engine_task_restart(request):
        """
        蓝图引擎任务重启接口
        :param request: 传过来蓝图实例ID
        :return:
        """
        msg_prefix = u"蓝图引擎实例重启接收"
        blue_instance_number = request.data.get("blue_instance_number")
        c_blue_ins_obj = BlueInstance.objects.filter(blue_instance_number=blue_instance_number).first()
        # 提取业务数据
        try:
            c_blue_ins_obj.status = 0
            c_blue_ins_obj.current_node = None
            c_blue_ins_obj.save()
            data = model_to_dict(c_blue_ins_obj)
            # 实例化
            # req_data = BLueEngine.blue_engine_control_center(data=data)
            # 异步
            req_data = blue_engine_control_center.delay(data=data)
            if req_data.id:
                # if celery_task_result_data.ready() == True:
                return Response({"status": 1, "msg": "蓝图正在重启中，请稍后", "data": data})

            if req_data['status'] == -1:
                msg = msg_prefix + u"失败， "
                return Response({"status": -1, "msg": msg, "data": req_data})
        except Exception as e:
            msg = msg_prefix + u"失败，错误信息" + unicode(e)
            return Response({"status": -1, "msg": msg, "data": {}})

        else:
            msg = msg_prefix + u"成功， 蓝图引擎重启接口"
            # 删除之前的错误的蓝图节点实例
            NodeInstance.objects.filter(blue_instance=c_blue_ins_obj).delete()

            return Response({"status": 1, "msg": msg, "data": req_data})

    @staticmethod
    @api_view(["POST"])
    def blue_engine_task_recover(request):
        """
        需要参数
        {
        "blue_instance_number": "",
        "current_note_id": "",
        }
        """
        '接收参数'

        req_data = post_data_to_dict(request.data)
        req = BLueEngine.fix_wrong_node_task(req_data)
        if req['status'] == -1:
            return Response({"status": -1, "msg": "恢复失败", "data": req})
        # print req
        if req['status'] == 1:
            return Response({"status": 1, "msg": "恢复执行成功，正在进行恢复", "data": req})
        # c_blue_ins_obj = BlueInstance.objects.filter(blue_instance_number=blue_instance_number).first()

    @staticmethod
    @api_view(["POST"])
    def blue_engine_instance(request):
        """
        此静态方法用于 蓝图引擎的蓝图实例化接口传递
        :param request: 接口接收的数据
        :return:
        """

        msg_prefix = u"蓝图实例接口接收"
        business_data_dict = request.data.get("business_data")
        map_relation_dict = request.data.get("map_relation")
        process_info_dict = request.data.get("process_info")
        if not business_data_dict:
            return Response({"status": -1, "msg": "business_data_dict", "data": []})
        submit_data_dict = business_data_dict.get("submit_data")
        submit_result_dict=business_data_dict.get("submit_result")

        if not submit_data_dict:
            return Response({"status": -1, "msg": "submit_data_dict", "data": []})

        host_config_data_list = submit_data_dict.get("host_config_data") # 配置数据
        format_dict  = {}
        format_dict['map_relation'] = map_relation_dict
        format_dict['process_info'] = process_info_dict

        format_dict['business_data'] = process_info_dict

        submit_info_dict = submit_data_dict.get("submit_info")  # 提交信息
        big_list = []
        for i in host_config_data_list:
            list1 = []
            list1.append(i)
            new_construction_dict = {}
            business_data_dict1 = {}
            new_construction_dict['map_relation'] = map_relation_dict
            new_construction_dict['process_info'] = process_info_dict
            business_data_dict1['submit_data'] = {"host_config_data":list1,"submit_info":submit_info_dict}
            business_data_dict1['submit_result'] = submit_result_dict

            new_construction_dict['business_data'] = business_data_dict1
            big_list.append(new_construction_dict)
        req_list = []
        for new_data in big_list:


            req_data = BLueEngine.task_blue_instance(request=request, data=new_data)
            if req_data["status"] == 1:
                msg = msg_prefix + u"成功!"
                blue_engine_logger.info(msg)
                blue_ins_data = req_data['data']['data']
                blue_instance_number_dict={}
                blue_instance_number_dict['blue_instance_number'] = blue_ins_data.get("blue_instance_number")

                # BLueEngine.blue_engine_control_center(data=blue_ins_data)
                # 异步调用调度中心

                celery_task_result_data = blue_engine_control_center.delay(data=blue_ins_data)
                if celery_task_result_data.id:
                    # if celery_task_result_data.ready() == True:
                    # msg = msg_prefix + u"成功!"
                    req_list.append(blue_instance_number_dict)
                    # return Response({"status": 1, "msg": msg, "data": req_data})
                else:
                    msg = msg_prefix + u"失败!"
                    return Response({"status": -1, "msg": msg, "data": []})
            else:
                msg = msg_prefix + u"创建失败!当前蓝图不可用"
                blue_engine_logger.warning(msg)
                return Response({"status": -1, "msg": msg, "data": req_data})
        if req_list:
            return Response({"status": 1, "msg": "蓝图引擎实例化调用成功", "data": req_list})
        else:
            return Response({"status": -1, "msg": "蓝图引擎实例化调用成功,传入数值错误", "data": []})

        # new_construction_dict = {}



        #
        # for i in big_list:
        #
        #     req_data = BLueEngine.task_blue_instance(request=request,data=i)


        # for i in host_config_data_list:
        #     # i 是每一个 主机的数据
        #     i_dict = {}
        #     i_dict.update(i)
        #     i_dict.update(submit_info_dict)
        #     list1.append(i_dict)

        # format_business_dict = {}
        # format_business_dict['submit_data'] = list1
        # format_business_dict['submit_result'] = submit_result_dict

        # format_dict['business_data'] = format_business_dict
        #
        # format_dict['business_data'] = list1
        #
        # # ori_data.get
        #
        #
        # return Response({"status": 1, "msg": "dddd", "data": format_dict})






        #####################源代码###########################################
        # try:
        #
        #     req_data = BLueEngine.task_blue_instance(request)
        # except Exception, e:
        #     msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        #     logger.error(format_exc())
        #
        # else:
        #
        #     if req_data["status"] == 1:
        #         msg = msg_prefix + u"成功!"
        #         blue_engine_logger.info(msg)
        #         blue_ins_data = req_data['data']['data']
        #
        #         # BLueEngine.blue_engine_control_center(data=blue_ins_data)
        #         # 异步调用调度中心
        #
        #         celery_task_result_data = blue_engine_control_center.delay(data=blue_ins_data)
        #         if  celery_task_result_data.id:
        #         # if celery_task_result_data.ready() == True:
        #             msg = msg_prefix + u"成功!"
        #             return Response({"status": 1, "msg": msg, "data": req_data})
        #         else:
        #             msg = msg_prefix + u"失败!"
        #             return Response({"status": -1, "msg": msg, "data": []})
        #         # if celery_task_result_data.get():
        #         #
        #         #     d1 = celery_task_result_data.get()
        #         #     req_status = d1['status']
        #         #     if req_status == -1:
        #         #         msg = msg_prefix + u"失败"
        #         #         logger.error(format_exc())
        #         #         blue_engine_logger.error(format_exc())
        #         #         blue_engine_task_logger.error(msg)
        #         #         return {"status": -1, "msg": msg, "data": d1}
        #         #     elif req_status == 1:
        #         #         msg = msg_prefix + u"成功!"
        #         #         return {"status": 1, "msg": msg, "data": d1}
        #         #     else:
        #         #         msg = msg_prefix + u"异常!"
        #         #         blue_engine_logger.error(format_exc())
        #         #         return {"status": -1, "msg": msg, "data": []}
        #         # return Response({"status": 1, "msg": msg, "data": req_data})
        #     else:
        #         msg = msg_prefix + u"创建失败!当前蓝图不可用"
        #         blue_engine_logger.warning(msg)
        #     return Response({"status": -1, "msg": msg, "data": req_data})

            #####################源代码###########################################

    @classmethod
    # @auto_log
    def task_blue_instance(cls, request,data, *args, **kwargs):
        """
        此方法用于 蓝图引擎的蓝图实例化接口
        :param request: 请求数据
        :return:
        """
        msg_prefix = "蓝图实例化任务"
        # try:
        # data = request.data
        data = data
        user = request.user
        d = BlueInstanceAPI(request)
        d1 = d.blue_instance(data)  # 蓝图实例任data务数据
        # d1 = d.blue_instance(request)  # 源代码
        req_status = d1.get('status')  # 任务的状态
        req_data = d1.get('data')
        req_msg = d1.get('msg')
        if req_status == -1:
            msg = msg_prefix + u"失败"
            logger.error(format_exc())
            blue_engine_logger.error(format_exc())
            return {"status": -1, "msg": msg, "data": d1}
        elif req_status == 1:
            msg = msg_prefix + u"成功!"
            blue_engine_task_logger.info(msg)
            # 任务成功，创建引擎日志记录
            # access_module_key = data.get('access_module_key')

            BlueEngineTask.objects.create(
                blue_instance_number=req_data['blue_instance_number'],
                # access_module_key=access_module_key,
                blue_print_id=req_data['blue_print'],
                user=user,
                task_progress=u'0%'
            )
            return {"status": 1, "msg": msg, "data": d1}
        else:
            msg = msg_prefix + u"异常!"
            return {"status": -1, "msg": msg, "data": []}

    # @classmethod
    # # @auto_log
    # def task_blue_instance_execute(cls, data, global_note_list=None, **kwargs):
    #     """
    #     此静态方法用于 蓝图实例执行任务，调用节点执行接口
    #     :return:
    #     """
    #     task_note_list = []
    #     msg_prefix = "蓝图实例执行任务"
    #     blue_ins_data = data
    #     if not blue_ins_data:
    #         msg = msg_prefix + "执行失败，没有数据"
    #         blue_engine_logger.error(format_exc())
    #         return {"status": -1, "msg": msg, "data": data}
    #     elif not blue_ins_data['avaliable_node_sort']:
    #         msg = msg_prefix + "执行失败，没有节点排序"
    #         blue_engine_logger.error(format_exc())
    #         return {"status": -1, "msg": msg, "data": data}
    #     d = BlueInstanceAPI(data)
    #     d1 = d.blue_note_instance(blue_ins_data)
    #     req_status = d1.get('status')
    #     if req_status == -1:
    #         msg = msg_prefix + u"失败"
    #         logger.error(format_exc())
    #         blue_engine_logger.error(format_exc())
    #         return {"status": -1, "msg": msg, "data": d1}
    #     elif req_status == 1:
    #         msg = msg_prefix + u"成功!"
    #         blue_engine_task_logger.info(msg)
    #         return {"status": 1, "msg": msg, "data": d1}
    #     else:
    #         msg = msg_prefix + u"异常!"
    #         blue_engine_logger.error(format_exc())
    #         blue_engine_task_logger.error(msg)
    #         return {"status": -1, "msg": msg, "data": []}
    #
    # @classmethod
    # # @auto_log
    # def task_blue_note_execute(cls, data, *args, **kwargs):
    #     """
    #     此 类方法 用于蓝图实例节点的执行任务
    #     :param data: 节点实例化数据
    #     :return:
    #     """
    #     msg_prefix = "节点执行任务"
    #     try:
    #         note_data = data['data']['data']
    #         input_params = note_data["node_input_entrance"]
    #         abs_url = note_data["url"]
    #         note_id = note_data["id"]
    #         # from iconfig import tasks
    #         # """
    #         # celery 异步执行部分
    #         # """
    #         # print " 执行节点执行任务"
    #         #
    #         # celery_task_result_data=tasks.blue_note_execute.delay(ori_data=note_data, data=input_params, url=abs_url, note_id=note_id)
    #         # print "执行节点执行任务"
    #         # if celery_task_result_data.status == "FAILURE":
    #         #     return {"status": -1, "msg": "celery任务执行失败", "data": []}
    #         # # print(celery_task_result_data.status)
    #         # # print(celery_task_result_data.info)
    #         # # print(celery_task_result_data.result)
    #         # """
    #         # [2019-08-02 01:57:48,880: INFO/MainProcess] Received task: iconfig.tasks.blue_note_execute[2bc85001-116e-4bfd-992e-8af00323fc93]
    #         # """
    #         # if celery_task_result_data.get():
    #         #
    #         #     d1 = celery_task_result_data.get()
    #         #     req_status = d1['status']
    #         #     if req_status == -1:
    #         #         msg = msg_prefix + u"失败"
    #         #         logger.error(format_exc())
    #         #         blue_engine_logger.error(format_exc())
    #         #         blue_engine_task_logger.error(msg)
    #         #         return {"status": -1, "msg": msg, "data": d1}
    #         #     elif req_status == 1:
    #         #         msg = msg_prefix + u"成功!"
    #         #         return {"status": 1, "msg": msg, "data": d1}
    #         #     else:
    #         #         msg = msg_prefix + u"异常!"
    #         #         blue_engine_logger.error(format_exc())
    #         #         return {"status": -1, "msg": msg, "data": []}
    #         # """
    #         # celery 异步执行部分
    #         # """
    #
    #         # [root@dCG013050 itmsp]# celery  worker -A itmsp -l debug
    #
    #         #
    #         # d1 = tasks.blue_note_execute(ori_data=note_data, data=input_params, url=abs_url, note_id=note_id)
    #         d = BlueInstanceAPI(data)
    #         d1 = d.blue_note_execute(ori_data=note_data, data=input_params, url=abs_url, note_id=note_id)
    #         #
    #         #
    #         #
    #         #
    #         # """
    #         # d1 = {u'status': 1, u'msg': u'\u514b\u9686\u865a\u62df\u673a \u6210\u529f!', u'data': {u'status': u'success'}}
    #         # """
    #         req_status = d1['data']['status']
    #         if req_status == -1:
    #             msg = msg_prefix + u"失败"
    #             logger.error(format_exc())
    #             blue_engine_logger.error(format_exc())
    #             blue_engine_task_logger.error(msg)
    #             return {"status": -1, "msg": msg, "data": d1}
    #         elif req_status == 1:
    #             msg = msg_prefix + u"成功!"
    #             return {"status": 1, "msg": msg, "data": d1}
    #         else:
    #             msg = msg_prefix + u"异常!"
    #             blue_engine_logger.error(format_exc())
    #             return {"status": -1, "msg": msg, "data": []}
    #     except Exception, e:
    #         msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
    #         logger.error(format_exc())
    #         blue_engine_task_logger.error(msg)
    #         return {"status": -1, "msg": msg, "data": []}
    #
    # @classmethod
    #
    # def task_blue_note_update(cls, data, last_data, **kwargs):
    #     """
    #
    #     :param data:
    #     :param args:
    #     :param kwargs:
    #     :return:
    #     """
    #     msg_prefix = "节点更新任务"
    #
    #     try:
    #         note_instance_data = data['data']
    #         print "节点更新任务" * 10
    #         print note_instance_data
    #         print "节点更新任务"* 10
    #         last_data1 = last_data['data']['data']
    #         d = BlueInstanceAPI(data)
    #         d1 = d.blue_note_update(ori_data=data, last_data=last_data1)  # data 为 上个任务的data
    #         req_status = d1['status']
    #         if not d1:
    #             msg = msg_prefix + u"失败"
    #             return {"status": -1, "msg": msg, "data": []}
    #
    #     except Exception, e:
    #         msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
    #         logger.error(format_exc())
    #         blue_engine_logger.error(format_exc())
    #         return {"status": -1, "msg": msg, "data": []}
    #     if req_status == -1:
    #         msg = msg_prefix + u"失败"
    #         logger.error(format_exc())
    #         blue_engine_logger.error(format_exc())
    #         return {"status": -1, "msg": msg, "data": d1}
    #     elif req_status == 1:
    #         msg = msg_prefix + u"成功!"
    #         return {"status": 1, "msg": msg, "data": d1}
    #     else:
    #         msg = msg_prefix + u"异常!"
    #         blue_engine_logger.error(format_exc())
    #         return {"status": -1, "msg": msg, "data": []}
    #
    # @classmethod
    # def blue_is_next_note(cls, data):
    #     """
    #
    #     :param data: 节点更新返回的数据 要根据其中的 remaining_notes 判断
    #     :return:
    #     """
    #     note_instance = data['data']['data']  # 应该是当前节点实例的数据
    #     blue_ins_id = data['data']['data']['blue_instance']
    #
    #     current_blue_instance_obj = BlueInstance.objects.filter(id=blue_ins_id).first()
    #     remaining_notes = data['data']['data']['remaining_notes']  # 应该是当前节点实例的数据
    #     print '应该是当前蓝图实例的的节点列表数据'
    #     print remaining_notes
    #     blue_instance_task_obj = BlueEngineTask.objects.filter(
    #         blue_instance_number=current_blue_instance_obj.blue_instance_number).first()
    #     if not remaining_notes:
    #         # print "进入直接结束"
    #         msg = '当前蓝图实例的节点全部完成'
    #         current_blue_instance_obj.status = 2
    #         start_time = blue_instance_task_obj.startTime
    #         start_time = start_time.replace(tzinfo=None)
    #         end_time = datetime.now()
    #
    #         current_blue_instance_obj.endTime = end_time
    #         current_blue_instance_obj.save()
    #         time_difference_sec = u"%s秒" % (end_time - start_time).seconds
    #         blue_instance_task_obj.task_elapsed_time = time_difference_sec
    #         blue_instance_task_obj.task_progress = "100%"
    #         blue_engine_task_logger.info("蓝图引擎任务调度完成,欢迎下次使用")
    #         str_log = str(tail.contents())
    #         blue_instance_task_obj.blue_engine_log = str_log
    #         blue_instance_task_obj.save()
    #         # current_blue_instance_obj
    #         '取出节点实例 并通过节点实例中的节点定义判断'
    #         node_ins_set = NodeInstance.objects.filter(blue_instance=current_blue_instance_obj).all()
    #         result_note_data_list = []
    #         for node_ins_obj in node_ins_set:
    #             # print '循环出节点实例对象， 判断'
    #             # print node_ins_obj.blue_node.downstream_node
    #
    #             data2 = model_to_dict(node_ins_obj.blue_node)
    #             # print data2
    #             if not data2['downstream_node']:
    #                 result_note_data_list.append(node_ins_obj.node_returns)
    #             # 循环出节点实例对象， 判断
    #             # result_note_data ={}
    #             # if not node_ins_obj.blue_node.downstream_node:
    #             # print node_ins_obj.node_returns
    #
    #         blue_instance_task_obj.result_data = result_note_data_list
    #         blue_instance_task_obj.save()
    #         data1 = model_to_dict(current_blue_instance_obj)
    #         return {"status": 1, "msg": msg, "data": data1}
    #     elif remaining_notes:
    #         print "对呀"
    #         data3 = {"remaining_notes": remaining_notes}
    #         data2 = model_to_dict(current_blue_instance_obj)
    #         data2.update(data3)
    #         # cls.task_blue_instance_execute(data=data2,global_note_list=remaining_notes)
    #         cls.blue_engine_control_center(data=data2)
    #
    #         return {"status": 2, "msg": '当前实例的节点完成，将进行下一个节点实例化任务', "data": data2}
    #
    @classmethod
    def fix_wrong_node_task(cls, data):
        """
        节点修复~
        :param data: 接口原装数据
        :return: 节点数据给
        """
        # data.get("")
        blue_ins_number = smart_get(data, "blue_instance_number", str)
        # blue_node = smart_get(data, "blue_node", str)
        '有几种情况'
        """
        读取当前蓝图实例和当前执行节点的列表
        获取当前节点 和剩余列表
        """
        blue_ins_obj = BlueInstance.objects.filter(blue_instance_number=blue_ins_number).first()
        if not blue_ins_obj:
            return {"status": -1, "msg": "暂无该蓝图实例", "data": data}
        # 获取完数据，提取处错误的节点
        from django.db.models import Q
        # 凡是不成功都是失败
        error_node_instance = NodeInstance.objects.filter(Q(blue_instance=blue_ins_obj) & ~Q(status=5)).first()
        if blue_ins_obj.status != 3:
            data = model_to_dict(blue_ins_obj)
            return {"status": -1, "msg": "当前蓝图正常，无法恢复", "data": data}
        if not error_node_instance:
            # 说明 还没实例化呢  ，没有实例化则要找到这个对应的节点定义的iD

            return {"status": -1, "msg": "当前蓝图节点暂无实例化，您可以尝试重启该实例", "data": []}
        else:
            if not error_node_instance.blue_node:
                return {"status": -1, "msg": "蓝图恢复失败，并无当前节点", "data": []}
            error_note_obj = error_node_instance.blue_node.id  # 节点对象

            list2 = blue_ins_obj.avaliable_node_sort[::-1]  # 倒叙列表
            remaining_notes = list2[:list2.index(error_note_obj) + 1]
            dict1 = {"remaining_notes": remaining_notes}
            data2 = model_to_dict(blue_ins_obj)
            data2.update(dict1)


            # req_data = cls.blue_engine_control_center(data=data2)
            # req_data = cls.blue_engine_control_center(data=data2)
            req_data = blue_engine_control_center.delay(data=data2)
            if req_data.id:
                # if celery_task_result_data.ready() == True:
                return {"status": 1, "msg": "蓝图恢复执行开始", "data": req_data}
            # if req_data['status'] == -1:
            #     return {"status": -1, "msg": "蓝图恢复失败", "data": req_data}
            return {"status": 1, "msg": "蓝图恢复正常", "data": req_data}
    #
    # @classmethod
    # # @auto_log
    # def blue_engine_control_center(cls, data):
    #     """
    #     蓝图引擎调度中心
    #
    #     :return:
    #     """
    #     msg_prefix = "任务调度"
    #     blue_instance_task_obj = ''
    #     try:
    #         if data:
    #             current_blue_ins_obj = BlueInstance.objects.filter(
    #                 blue_instance_number=data['blue_instance_number']).first()
    #             msg = msg_prefix + u"成功!，将进行蓝图实例执行任务"
    #             task_blue_instance_execute_data = cls.task_blue_instance_execute(data=data)
    #             print task_blue_instance_execute_data
    #             blue_engine_task_logger.info(msg)
    #             str_log = str(tail.contents())
    #             is_blue_instance_task_obj = BlueEngineTask.objects.filter(
    #                 blue_instance_number=data['blue_instance_number']).first()
    #             if is_blue_instance_task_obj:
    #                 blue_instance_task_obj = is_blue_instance_task_obj
    #                 blue_instance_task_obj.blue_engine_log = str_log
    #
    #                 blue_instance_task_obj.save()
    #             if task_blue_instance_execute_data['status'] == -1:
    #                 msg = msg_prefix + u"失败!" + task_blue_instance_execute_data['msg']
    #                 blue_engine_logger.error(format_exc())
    #                 blue_engine_task_logger.error(msg)
    #                 str_log = str(tail.contents())
    #                 blue_instance_task_obj.blue_engine_log = str_log
    #                 blue_instance_task_obj.save()
    #                 current_blue_ins_obj.status = 3
    #                 current_blue_ins_obj.save()
    #                 return {"status": -1, "msg": msg, "data": task_blue_instance_execute_data}
    #             elif task_blue_instance_execute_data['status'] == 1:
    #                 msg = msg_prefix + u"成功!，将进行节点执行任务"
    #                 blue_engine_task_logger.info(msg)
    #                 str_log = str(tail.contents())
    #                 blue_instance_task_obj.blue_engine_log = str_log
    #                 blue_instance_task_obj.task_progress = '25%'
    #                 blue_instance_task_obj.save()
    #                 task_blue_note_execute_return_data = cls.task_blue_note_execute(task_blue_instance_execute_data)
    #
    #                 if task_blue_note_execute_return_data['status'] == -1:
    #                     msg = msg_prefix + u"失败"
    #                     blue_engine_task_logger.error(msg)
    #                     str_log = str(tail.contents())
    #                     blue_instance_task_obj.blue_engine_log = str_log
    #                     blue_instance_task_obj.save()
    #                     current_blue_ins_obj.status = 3
    #                     current_blue_ins_obj.save()
    #                     return {"status": -1, "msg": msg, "data": task_blue_note_execute_return_data}
    #                 elif task_blue_note_execute_return_data['status'] == 1:
    #                     # print '?' * 100
    #                     msg = msg_prefix + u"成功!，将进入节点更新任务"
    #
    #                     blue_engine_task_logger.info(msg)
    #                     str_log = str(tail.contents())
    #                     blue_instance_task_obj.blue_engine_log = str_log
    #                     blue_instance_task_obj.task_progress = '50%'
    #                     blue_instance_task_obj.save()
    #                     task_req_data = cls.task_blue_note_update(data=task_blue_instance_execute_data,
    #                                                               last_data=task_blue_note_execute_return_data)  # 节点更新任务
    #
    #                     if task_req_data['status'] == -1:
    #                         msg = msg_prefix + u"节点更新任务失败!"
    #                         blue_engine_task_logger.error(msg)
    #                         str_log = str(tail.contents())
    #                         blue_instance_task_obj.blue_engine_log = str_log
    #                         blue_instance_task_obj.save()
    #                         current_blue_ins_obj.status = 3
    #                         current_blue_ins_obj.save()
    #                         return {"status": -1, "msg": msg, "data": task_req_data}
    #                     elif task_req_data['status'] == 1:
    #                         msg = msg_prefix + u"节点更新任务成功!"
    #                         blue_engine_task_logger.info(msg)
    #                         str_log = str(tail.contents())
    #                         blue_instance_task_obj.blue_engine_log = str_log
    #                         blue_instance_task_obj.task_progress = '75%'
    #                         blue_instance_task_obj.save()
    #                         # 当一个节点执行完完毕之后，需要判断 当前 蓝图实例剩余的可执行的节点，并重新治实例化节点
    #                         req_data = cls.blue_is_next_note(task_req_data)
    #                         if req_data['status'] == 1:
    #                             msg = msg_prefix + u"节点判断任务成功!,任务成功"
    #                             blue_engine_task_logger.info(msg)
    #                             str_log = str(tail.contents())
    #                             blue_instance_task_obj.blue_engine_log = str_log
    #                             blue_instance_task_obj.task_progress = '100%'
    #                             blue_instance_task_obj.save()
    #                             return {"status": 1, "msg": msg, "data": []}
    #                         elif req_data['status'] == 2:
    #                             req_data = cls.blue_is_next_note(task_req_data)
    #                     return {"status": 1, "msg": msg, "data": task_req_data}
    #     except Exception, e:
    #         msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
    #         logger.error(format_exc())
    #         blue_engine_logger.error(format_exc())
    #         return {"status": -1, "msg": msg, "data": {}}
