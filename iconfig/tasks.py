# coding: utf-8
# Author: Chery Huo
from itmsp.celery import app

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
import json
list1 = []
blue_engine_logger = set_log(LOG_LEVEL)




def task_blue_instance_execute(data, global_note_list=None, **kwargs):
    """
    此静态方法用于 蓝图实例执行任务，调用节点执行接口
    :return:
    """
    task_note_list = []
    msg_prefix = "蓝图实例执行任务"
    blue_ins_data = data
    if not blue_ins_data:
        msg = msg_prefix + "执行失败，没有数据"
        blue_engine_logger.error(format_exc())
        return {"status": -1, "msg": msg, "data": data}
    elif not blue_ins_data['avaliable_node_sort']:
        msg = msg_prefix + "执行失败，没有节点排序"
        blue_engine_logger.error(format_exc())
        return {"status": -1, "msg": msg, "data": data}
    d = BlueInstanceAPI(data)
    print "节点实例化接口返回值"
    print blue_ins_data
    print "节点实例化接口返回值"
    d1 = d.blue_note_instance(blue_ins_data)
    print "节点实例化接口返回值"
    print d1
    print "节点实例化接口返回值"

    req_status = d1.get('status')
    if req_status == -1:
        msg = msg_prefix + u"失败"
        logger.error(format_exc())
        blue_engine_logger.error(format_exc())
        return {"status": -1, "msg": msg, "data": d1}
    elif req_status == 1:
        msg = msg_prefix + u"成功!"
        blue_engine_task_logger.info(msg)
        return {"status": 1, "msg": msg, "data": d1}
    else:
        msg = msg_prefix + u"异常!"
        blue_engine_logger.error(format_exc())
        blue_engine_task_logger.error(msg)
        return {"status": -1, "msg": msg, "data": []}




def task_blue_note_execute(data, *args, **kwargs):
    """
    此 类方法 用于蓝图实例节点的执行任务
    :param data: 节点实例化数据
    :return:
    """
    msg_prefix = "节点执行任务"
    try:
        note_data = data['data']['data']
        input_params = note_data["node_input_entrance"]
        abs_url = note_data["url"]
        note_id = note_data["id"]
        # from iconfig import tasks
        # """
        # celery 异步执行部分
        # """
        # print " 执行节点执行任务"
        #
        # celery_task_result_data=tasks.blue_note_execute.delay(ori_data=note_data, data=input_params, url=abs_url, note_id=note_id)
        # print "执行节点执行任务"
        # if celery_task_result_data.status == "FAILURE":
        #     return {"status": -1, "msg": "celery任务执行失败", "data": []}
        # # print(celery_task_result_data.status)
        # # print(celery_task_result_data.info)
        # # print(celery_task_result_data.result)
        # """
        # [2019-08-02 01:57:48,880: INFO/MainProcess] Received task: iconfig.tasks.blue_note_execute[2bc85001-116e-4bfd-992e-8af00323fc93]
        # """
        # if celery_task_result_data.get():
        #
        #     d1 = celery_task_result_data.get()
        #     req_status = d1['status']
        #     if req_status == -1:
        #         msg = msg_prefix + u"失败"
        #         logger.error(format_exc())
        #         blue_engine_logger.error(format_exc())
        #         blue_engine_task_logger.error(msg)
        #         return {"status": -1, "msg": msg, "data": d1}
        #     elif req_status == 1:
        #         msg = msg_prefix + u"成功!"
        #         return {"status": 1, "msg": msg, "data": d1}
        #     else:
        #         msg = msg_prefix + u"异常!"
        #         blue_engine_logger.error(format_exc())
        #         return {"status": -1, "msg": msg, "data": []}
        # """
        # celery 异步执行部分
        # """

        # [root@dCG013050 itmsp]# celery  worker -A itmsp -l debug

        #
        # d1 = tasks.blue_note_execute(ori_data=note_data, data=input_params, url=abs_url, note_id=note_id)
        d = BlueInstanceAPI(data)
        d1 = d.blue_note_execute(ori_data=note_data, data=input_params, url=abs_url, note_id=note_id)
        #
        #
        #
        #
        # """
        # d1 = {u'status': 1, u'msg': u'\u514b\u9686\u865a\u62df\u673a \u6210\u529f!', u'data': {u'status': u'success'}}
        # """
        req_status = d1['status']
        if req_status == -1:
            msg = msg_prefix + u"失败"
            logger.error(format_exc())
            blue_engine_logger.error(format_exc())
            blue_engine_task_logger.error(msg)
            return {"status": -1, "msg": msg, "data": d1}
        elif req_status == 1:
            msg = msg_prefix + u"成功!"
            return {"status": 1, "msg": msg, "data": d1}
        else:
            msg = msg_prefix + u"异常!"
            blue_engine_logger.error(format_exc())
            return {"status": -1, "msg": msg, "data": []}
    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        blue_engine_task_logger.error(msg)
        return {"status": -1, "msg": msg, "data": []}



def task_blue_note_update(data, last_data, **kwargs):
    """

    :param data:
    :param args:
    :param kwargs:
    :return:
    """
    msg_prefix = "节点更新任务"

    try:
        note_instance_data = data['data']
        print "节点更新任务" * 10
        print note_instance_data
        print "节点更新任务" * 10
        last_data1 = last_data['data']['data']
        d = BlueInstanceAPI(data)
        d1 = d.blue_note_update(ori_data=data, last_data=last_data1)  # data 为 上个任务的data
        req_status = d1['status']
        if not d1:
            msg = msg_prefix + u"失败"
            return {"status": -1, "msg": msg, "data": []}

    except Exception, e:
        msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        blue_engine_logger.error(format_exc())
        return {"status": -1, "msg": msg, "data": []}
    if req_status == -1:
        msg = msg_prefix + u"失败"
        logger.error(format_exc())
        blue_engine_logger.error(format_exc())
        return {"status": -1, "msg": msg, "data": d1}
    elif req_status == 1:
        msg = msg_prefix + u"成功!"
        return {"status": 1, "msg": msg, "data": d1}
    else:
        msg = msg_prefix + u"异常!"
        blue_engine_logger.error(format_exc())
        return {"status": -1, "msg": msg, "data": []}



def blue_is_next_note(data):
    """

    :param data: 节点更新返回的数据 要根据其中的 remaining_notes 判断
    :return:
    """
    note_instance = data['data']['data']  # 应该是当前节点实例的数据
    blue_ins_id = data['data']['data']['blue_instance']

    current_blue_instance_obj = BlueInstance.objects.filter(id=blue_ins_id).first()
    remaining_notes = data['data']['data']['remaining_notes']  # 应该是当前节点实例的数据
    print '当前蓝图实例的的节点列表数据'
    print remaining_notes
    blue_instance_task_obj = BlueEngineTask.objects.filter(
        blue_instance_number=current_blue_instance_obj.blue_instance_number).first()
    if not remaining_notes:
        # print "进入直接结束"
        msg = '当前蓝图实例的节点全部完成'
        current_blue_instance_obj.status = 2
        start_time = blue_instance_task_obj.startTime
        start_time = start_time.replace(tzinfo=None)
        end_time = datetime.now()

        current_blue_instance_obj.endTime = end_time
        current_blue_instance_obj.save()
        time_difference_sec = u"%s秒" % (end_time - start_time).seconds
        blue_instance_task_obj.task_elapsed_time = time_difference_sec
        blue_instance_task_obj.task_progress = "100%"
        blue_engine_task_logger.info("蓝图引擎任务调度完成,欢迎下次使用")
        str_log = str(tail.contents())
        blue_instance_task_obj.blue_engine_log = str_log
        blue_instance_task_obj.save()
        # current_blue_instance_obj
        '取出节点实例 并通过节点实例中的节点定义判断'
        node_ins_set = NodeInstance.objects.filter(blue_instance=current_blue_instance_obj).all()
        result_note_data_list = []
        for node_ins_obj in node_ins_set:
            # print '循环出节点实例对象， 判断'
            # print node_ins_obj.blue_node.downstream_node

            data2 = model_to_dict(node_ins_obj.blue_node)
            # print data2
            if not data2['downstream_node']:
                result_note_data_list.append(node_ins_obj.node_returns)
            # 循环出节点实例对象， 判断
            # result_note_data ={}
            # if not node_ins_obj.blue_node.downstream_node:
            # print node_ins_obj.node_returns

        blue_instance_task_obj.result_data = result_note_data_list
        blue_instance_task_obj.save()
        data1 = model_to_dict(current_blue_instance_obj)
        return {"status": 1, "msg": msg, "data": data1}
    elif remaining_notes:
        print "对呀"
        data3 = {"remaining_notes": remaining_notes}
        data2 = model_to_dict(current_blue_instance_obj)
        data2.update(data3)
        # cls.task_blue_instance_execute(data=data2,global_note_list=remaining_notes)
        blue_engine_control_center(data=data2)

        return {"status": 2, "msg": '当前实例的节点完成，将进行下一个节点实例化任务', "data": data2}


@app.task
def blue_engine_control_center(data):
        """
        蓝图引擎调度中心

        :return:
        """
        msg_prefix = "任务调度"
        blue_instance_task_obj = ''
        try:
            if data:
                current_blue_ins_obj = BlueInstance.objects.filter(
                    blue_instance_number=data['blue_instance_number']).first()
                msg = msg_prefix + u"成功!，将进行蓝图实例执行任务"
                task_blue_instance_execute_data = task_blue_instance_execute(data=data)
                print task_blue_instance_execute_data
                blue_engine_task_logger.info(msg)
                str_log = str(tail.contents())
                is_blue_instance_task_obj = BlueEngineTask.objects.filter(
                    blue_instance_number=data['blue_instance_number']).first()
                if is_blue_instance_task_obj:
                    blue_instance_task_obj = is_blue_instance_task_obj
                    blue_instance_task_obj.blue_engine_log = str_log

                    blue_instance_task_obj.save()
                if task_blue_instance_execute_data['status'] == -1:
                    msg = msg_prefix + u"失败!" + task_blue_instance_execute_data['msg']
                    blue_engine_logger.error(format_exc())
                    blue_engine_task_logger.error(msg)
                    str_log = str(tail.contents())
                    blue_instance_task_obj.blue_engine_log = str_log
                    blue_instance_task_obj.save()
                    current_blue_ins_obj.status = 3
                    current_blue_ins_obj.save()
                    return {"status": -1, "msg": msg, "data": task_blue_instance_execute_data}
                elif task_blue_instance_execute_data['status'] == 1:
                    msg = msg_prefix + u"成功!，将进行节点执行任务"
                    blue_ins_status = current_blue_ins_obj.status
                    if blue_ins_status==3:
                        return {"status": -1, "msg": "蓝图检测异常无法进行下一步操作", "data": []}
                    blue_engine_task_logger.info(msg)
                    str_log = str(tail.contents())
                    blue_instance_task_obj.blue_engine_log = str_log
                    blue_instance_task_obj.task_progress = '25%'
                    blue_instance_task_obj.save()
                    task_blue_note_execute_return_data = task_blue_note_execute(task_blue_instance_execute_data)
                    # print "查看节点执行回来的东西"
                    # print task_blue_note_execute_return_data
                    # print "查看节点执行回来的东西"

                    if task_blue_note_execute_return_data['status'] == -1:
                        msg = msg_prefix + u"失败"
                        blue_engine_task_logger.error(msg)
                        str_log = str(tail.contents())
                        blue_instance_task_obj.blue_engine_log = str_log
                        blue_instance_task_obj.save()
                        current_blue_ins_obj.status = 3
                        current_blue_ins_obj.save()
                        return {"status": -1, "msg": msg, "data": task_blue_note_execute_return_data}
                    elif task_blue_note_execute_return_data['status'] == 1:
                        # print '?' * 100
                        msg = msg_prefix + u"成功!，将进入节点更新任务"

                        blue_engine_task_logger.info(msg)
                        str_log = str(tail.contents())
                        blue_instance_task_obj.blue_engine_log = str_log
                        blue_instance_task_obj.task_progress = '50%'
                        blue_instance_task_obj.save()
                        task_req_data = task_blue_note_update(data=task_blue_instance_execute_data,
                                                                  last_data=task_blue_note_execute_return_data)  # 节点更新任务

                        if task_req_data['status'] == -1:
                            msg = msg_prefix + u"节点更新任务失败!"
                            blue_engine_task_logger.error(msg)
                            str_log = str(tail.contents())
                            blue_instance_task_obj.blue_engine_log = str_log
                            blue_instance_task_obj.save()
                            current_blue_ins_obj.status = 3
                            current_blue_ins_obj.save()
                            return {"status": -1, "msg": msg, "data": task_req_data}
                        elif task_req_data['status'] == 1:
                            msg = msg_prefix + u"节点更新任务成功!"
                            blue_engine_task_logger.info(msg)
                            str_log = str(tail.contents())
                            blue_instance_task_obj.blue_engine_log = str_log
                            blue_instance_task_obj.task_progress = '75%'
                            blue_instance_task_obj.save()
                            # 当一个节点执行完完毕之后，需要判断 当前 蓝图实例剩余的可执行的节点，并重新治实例化节点
                            req_data = blue_is_next_note(task_req_data)
                            if req_data['status'] == 1:
                                msg = msg_prefix + u"节点判断任务成功!,任务成功"
                                blue_engine_task_logger.info(msg)
                                str_log = str(tail.contents())
                                blue_instance_task_obj.blue_engine_log = str_log
                                blue_instance_task_obj.task_progress = '100%'
                                blue_instance_task_obj.save()
                                return {"status": 1, "msg": msg, "data": []}
                            elif req_data['status'] == 2:
                                req_data = blue_is_next_note(task_req_data)
                        return {"status": 1, "msg": msg, "data": task_req_data}
        except Exception, e:
            msg = msg_prefix + u"失败, 错误信息: " + unicode(e)
            logger.error(format_exc())
            blue_engine_logger.error(format_exc())
            return {"status": -1, "msg": msg, "data": {}}


def blue_note_execute(ori_data, data, url, note_id=None):
    """
    :param data:
    :param url::
    :param url:
    :param note_id:
    :return:
    """
    print "*" * 100
    print data
    print "*" * 100
    error_mag = ''
    current_note_instance_obj = NodeInstance.objects.filter(id=note_id).first()
    current_note_instance_obj.status = 3  # 开始执行
    current_note_instance_obj.save()
    msg_prefix = u'节点执行'
    # print '节点执行'
    import requests
    # headers = {'Connection': 'close', }
    # authorization = request.META.get('HTTP_AUTHORIZATION')
    headers = {'content-type': 'application/json', }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    error_mag1 = ''
    if r.status_code == 500:
        error_mag = r.json()
        error_mag1 = error_mag.get("msg")
    try:
        print "^" * 20
        # error_mag1
        print r.json()
        print error_mag1
        # if r.json():


        # return_data = r.text
        # print "^" * 20
        #
        # print "^" * 20
        return_data ={}

        if r.json():
            return_data = r.json()
        # return_data= json.dumps(return_data)

        remaining_notes = ori_data['remaining_notes']
        data1 = {'remaining_notes': remaining_notes}
        if r.raise_for_status():
            current_note_instance_obj.status = 6  # 开始执行
            current_note_instance_obj.save()
            return {"status": -1, "msg": "执行异常", "data": []}
        # print "!" * 100
        # print return_data
        """
        {u'status': 1, u'msg': u'\u514b\u9686\u865a\u62df\u673a \u6210\u529f!', u'data': {u'status': u'success'}}

        """
        print "!" * 100
        return_data.update(data1)
        if not return_data:
            current_note_instance_obj.status = 6  # 开始执行
            current_note_instance_obj.save()
            current_note_instance_obj.blue_instance.status=3
            current_note_instance_obj.blue_instance.save()
            print "接口执行失败"
            return {"status": -1, "msg": "接口执行失败", "data": []}
        # print r.json()
        return {"status": 1, "msg": "接口信息发送成功", "data": return_data}


    except Exception, e:

        msg = msg_prefix + u"失败, 错误信息: " + unicode(e) + error_mag1
        print msg
        logger.error(format_exc())
        current_note_instance_obj.status = 6  # 开始执行
        current_note_instance_obj.save()
        return Response({"status": -1, "msg": msg, "data": {}})
