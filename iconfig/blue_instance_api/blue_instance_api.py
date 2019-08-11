# coding: utf-8
# Author: Chery Huo

# from rest_framework.response import Response
from datetime import datetime
from iuser.permissions import *
from traceback import format_exc
from iconfig.models import *
from django.forms.models import model_to_dict
from iuser.models import ExUser
from itmsp.utils.base import set_log, smart_get, LOG_LEVEL
import json
import requests
blue_engine_logger = set_log(LOG_LEVEL)


class BlueInstanceAPI(object):
    """
    此API类用于蓝图引擎实际调用
    """

    def __init__(self, request):
        self.request = request
        self.global_note_list1 = []

    def blue_instance(self, data, *args, **kwargs):
        """
        蓝图实例化函数
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = "蓝图实例化"
        req_data = data #  新代码
        # req_data = self.request.data # 源代码

        # print req_data
        user = self.request.user.name
        try:
            import time
            NOW = time.strftime("%Y%m%d", time.localtime())  # 年月日
            instance_set = BlueInstance.objects.all()
            instance_len = len(instance_set)
            i = 1
            i += instance_len
            k = "%04d" % i
            format_number = u"blue" + NOW + k
            user = ExUser.objects.get(name=user)
            # print req_data

            blue_print_id = ''
            instance_number = ''

            map_relation_dict = req_data.get("map_relation")
            is_saved_print_id = req_data.get("blue_print_id")
            business_data_dict = req_data.get("business_data")
            if business_data_dict:
                submit_data_dict = business_data_dict.get("submit_data")
                host_config_data_list = submit_data_dict.get("host_config_data")
                if host_config_data_list:
                    instance_number = len(host_config_data_list)

            if map_relation_dict:

                blue_print_id = map_relation_dict.get("blue_print_id")
                # access_module_key = map_relation_dict.get("synthesize_code")
            elif is_saved_print_id:

                blue_print_id = is_saved_print_id
            else:
                return {"status": -1, "msg": "fdsfdsf", "data": []}
            print blue_print_id

            # if not map_relation_dict:
            #     return {"status": -1, "msg": '错误', "data": []}
            # blue_print_id = map_relation_dict.get("blue_print_id")
            blue = BluePrintDefinition.objects.filter(id=blue_print_id).first()
            print  blue
            if not blue:
                return {"status": -1, "msg": "不存在蓝图", "data": []}
            # 需要判断传入的蓝图是否是冻结的
            # if blue.is_valid == 0:
            #     # 未验证
            #     msg = msg_prefix + u"失败，当前蓝图未验证"
            #     return {"status": -1, "msg": msg, "data": []}
            if blue.is_valid == 2:

                msg = msg_prefix + u"失败，当前蓝图无效"
                return {"status": -1, "msg": msg, "data": []}
            elif blue.is_freeze:
                print blue.is_freeze
                msg = msg_prefix + u"失败，当前蓝图被冻结，请确认激活"
                return {"status": -1, "msg": msg, "data": []}
            elif not blue.is_freeze:
                # 校验有效 并且已经激活了
                # if not  instance_number: #
                current_obj = BlueInstance.objects.create(
                    blue_instance_number=format_number,
                    blue_print=blue,
                    user=user,
                    avaliable_node_sort=blue.avaliable_node_sort
                )
                data = model_to_dict(current_obj)
                if current_obj:
                    # map_relation_dict.get("blue_print_id")
                    # access_module_key = req_data.get('access_module_key')

                    business_data = req_data.get('business_data')
                    BlueAccessModuleParamsInstance.objects.create(
                        blue_instance_number=current_obj.blue_instance_number,
                        # access_module_key=access_module_key, # 按钮的综合编码
                        blue_print=current_obj.blue_print_id,
                        user=current_obj.user,
                        business_data=business_data,
                    )

                    data = model_to_dict(current_obj)
                msg = msg_prefix + u'成功'
                return {"status": 1, "msg": msg, "data": data}
                # else:
                #     i = 0
                #     while i<instance_number:

        except Exception, e:
            msg = msg_prefix + u"失败，错误:" + unicode(e)
            logger.error(format_exc())
            return {"status": -1, "msg": msg, "data": []}
        else:
            if not blue:
                return {"status": -1, "msg": "没有当前蓝图，实例化执行失败", "data": []}

    def blue_note_instance(self, data):
        """
        此方法为节点实例化和执行
                节点实例化步骤：
            0. 获取蓝图实例ID（节点定义ID，节点顺序）
            1.修改可执行节点的顺序
            2. 修改蓝图状态和当前节点
        :param data:
        :param args:
        :param kwargs:
        :return:
        """
        msg_prefix = "蓝图节点实例化"

        data = data  # 蓝图实例的数据
        print "我是API接口数据"
        print data
        blue_instance_number = data['blue_instance_number']
        available_node_list = data['avaliable_node_sort']
        remaining_notes1 = []
        # print available_node_list
        # print global_note_list1
        blue_instance_id = data['id']
        current_note_int_id = ''
        # if not  self.global_note_list:
        # if not data[remaining_notes]global_note_list1:
        if 'remaining_notes' not in data:
            # remaining_notes1=data["remaining_notes"]
            task_note_list = available_node_list[::-1]  # 翻转列表
            global_note_list = task_note_list

            print global_note_list
            current_note_int_id = global_note_list.pop()
            print global_note_list
        # elif global_note_list1:
        elif data['remaining_notes']:
            global_note_list = data['remaining_notes']
            current_note_int_id = global_note_list.pop()

        # '节点开始实例化'
        print "当前需要实例化的节点"
        print current_note_int_id
        blue_note_print_obj = BlueNodeDefinition.objects.filter(id=current_note_int_id).first()
        # print blue_note_print_obj
        blue_instance_obj = BlueInstance.objects.filter(id=blue_instance_id).first()
        if not blue_note_print_obj:
            msg = msg_prefix + u'失败,当前节点不可实例化'
            blue_engine_logger.error(format_exc())
            blue_engine_logger.warning(msg)
            blue_instance_obj.status = 3
            blue_instance_obj.save()
            # data1 = model_to_dict(blue_note_print_obj)
            return {"status": -1, "msg": msg, "data": []}
        '修改蓝图实例状态'
        blue_instance_obj.status = 1
        blue_instance_obj.current_node = blue_note_print_obj
        blue_instance_obj.save()
        # print blue_note_print_obj.component_data['url']
        # 创建节点实例
        url = blue_note_print_obj.component_data['url']
        new_note_instance_obj = NodeInstance.objects.create(node_instance_name=blue_note_print_obj.name,
                                                            blue_instance=blue_instance_obj,
                                                            blue_node=blue_note_print_obj,
                                                            url=url
                                                            )
        if not new_note_instance_obj:
            msg = msg_prefix + "失败， 创建实例失败"
            blue_engine_logger.warning(msg)
            return {"status": 1, "msg": msg, "data": []}

        '节点实例化了需要节点参数匹配'
        blue_note_params_query_return_data = self.blue_note_params_query(blue_note_id=current_note_int_id,
                                                                         note_instance=new_note_instance_obj)
        try:
            if blue_note_params_query_return_data['status'] == 1:  # 参数匹配成功
                new_note_instance_obj.status = 2  #
                new_note_instance_obj.node_input_entrance = blue_note_params_query_return_data['data']
                new_note_instance_obj.save()
            else:
                msg = msg_prefix + u'失败，节点参数匹配失败'
                new_note_instance_obj.status = 6
                new_note_instance_obj.save()
                return {"status": -1, "msg": msg, "data": []}
        except Exception, e:
            msg = msg_prefix + u"失败，错误:" + unicode(e)
            logger.error(format_exc())
            new_note_instance_obj.status = 6
            new_note_instance_obj.save()
            return {"status": -1, "msg": msg, "data": []}

        msg = msg_prefix + u'成功'
        data1 = {"remaining_notes": global_note_list}
        ret_data = model_to_dict(new_note_instance_obj)
        ret_data.update(data1)
        return {"status": 1, "msg": msg, "data": ret_data}

    def blue_note_params_query(self, blue_note_id, note_instance=None):
        """
        节点参数匹配
        :return:
        """
        msg_prefix = "节点参数匹配函数"
        blue_target_note_queryset = BlueNodeMapParam.objects.filter(target_node=blue_note_id).all()
        print '取出目标节点的集合'
        print blue_target_note_queryset
        if not blue_target_note_queryset:
            msg = msg_prefix + "失败"
            return {"status": -1, "msg": msg, "data": []}
        return_data = {}
        for blue_note_query_obj in blue_target_note_queryset:
            source_node_obj = BlueNodeDefinition.objects.filter(id=blue_note_query_obj.source_node).first()
            # print source_node_obj.name
            if source_node_obj.component_type == 0:  # 判断是否为接口
                # print '取上一个节点实例,并将输出 放到当前实例的输入中'
                # print note_instance.blue_instance
                last_note_instance = NodeInstance.objects.filter(blue_instance=note_instance.blue_instance,
                                                                 blue_node=source_node_obj).first()
                # print last_note_instance.node_instance_name
                last_data = last_note_instance.node_returns  # 上一个节点实例的返回值

                if blue_note_query_obj.source_param_name in last_data:
                    return_data[blue_note_query_obj.target_param_name] = last_data[
                        blue_note_query_obj.source_param_name]
                # else:
                #     msg = msg_prefix + "失败，参数匹配失败"
                #     return {"status": -1, "msg": msg, "data": []}


            elif source_node_obj.component_type == 1:  # 判断是否为参数
                params_dict = source_node_obj.component_data['params']
                for i in params_dict:
                    if blue_note_query_obj.source_param_name in i['param_name']:
                        return_data[blue_note_query_obj.target_param_name] = i['value']
                    # else:
                    #     msg = msg_prefix + "失败，参数匹配失败"
                    #     return {"status": -1, "msg": msg, "data": []}

            elif source_node_obj.component_type == 2:  # 判断是否为模块
                print "判断是否为模块"
                blue_access_obj = BlueAccessModuleParamsInstance.objects.filter(
                    blue_instance_number=note_instance.blue_instance.blue_instance_number).first()
                # print blue_access_obj
                submit_data_dict = blue_access_obj.business_data.get("submit_data")
                # print "打印出申请数据中的参数"
                #
                # print "打印出申请数据中的参数"
                if not submit_data_dict:
                    return {"status": -1, "msg": "当前业务数据无效", "data": []}
                host_config_dict = submit_data_dict.get("host_config_data")
                print "打印出申请数据中的参数"
                print host_config_dict
                print "打印出申请数据中的参数"
                if not host_config_dict:
                    return {"status": -1, "msg": "当前业务数据无效", "data": []}
                print "获取目标参数"
                print host_config_dict[0], type(host_config_dict)
                print host_config_dict[0].get("vc_ip"), type(host_config_dict[0])
                print blue_note_query_obj.source_param_name
                print "获取目标参数"
                if blue_note_query_obj.source_param_name in host_config_dict[0]:
                    print "哈哈哈哈"
                    print blue_note_query_obj.target_param_name
                    return_data[blue_note_query_obj.target_param_name] = host_config_dict[0][
                        blue_note_query_obj.source_param_name]
                else:
                    msg = msg_prefix + "失败，参数匹配失败"

                    return {"status": -1, "msg": msg, "data": []}
            elif source_node_obj.component_type == 3:  # 判断是否为蓝图
                pass
        # print "%" * 100
        # print return_data
        # print "%" * 100
        return {"status": 1, "msg": "参数匹配成功", "data": return_data}

    def blue_note_update(self, ori_data, last_data):
        msg_prefix = "节点更新函数"
        blue_note_instance_id = ori_data['data']['data']['id']
        current_note_instance_obj = NodeInstance.objects.filter(id=blue_note_instance_id).first()
        try:
            """
            本函数用于节点更新,用于添加节点实例的返回值和修改节点状态,
            需要输入参数:
                blue_note_instance_id; 节点实例的ID
                data : 上个任务数据
            """
            print "当前任务数据"
            print ori_data
            print "当前任务数据"
            current_note_instance_obj.status = 3  # 开始执行
            current_note_instance_obj.save()
            note_req_data = last_data["data"]  # 取回节点执行的返回的字典
            current_note_instance_obj.status = 4  # 输出参数回填
            current_note_instance_obj.save()
            current_note_instance_obj.node_returns = note_req_data
            current_note_instance_obj.status = 5  # 结束
            now = datetime.now()
            current_note_instance_obj.endTime = now
            current_note_instance_obj.save()
            remaining_notes = ori_data['data']['data']['remaining_notes']
            data2 = {"remaining_notes": remaining_notes}
            data1 = model_to_dict(current_note_instance_obj)
            data1.update(data2)

        except Exception, e:
            msg = msg_prefix + "失败,错误信息:" + unicode(e)
            logger.error(format_exc())
            current_note_instance_obj.status = 6  # 结束
            current_note_instance_obj.save()
            return {"status": -1, "msg": msg, "data": []}
        else:
            msg = msg_prefix + u"成功!"
            return {"status": 1, "msg": msg, "data": data1}

    def blue_note_execute(self,ori_data, data, url, note_id=None):
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
        #
        # s = requests.session()
        # s.keep_alive =False


        headers = {'content-type': 'application/json', "Connection":"close"}
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
            return {"status": -1, "msg": msg, "data": {}}
