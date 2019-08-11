# coding: utf-8
# Author: ld


from rest_framework import serializers
from .models import *
from itmsp.serializers import ChoiceDisplayField
from iworkflow.models import ProcessDefinition, TaskDefinition
from iconfig.models import BluePrintDefinition
import re


class ServerMenuCategorySerializer(serializers.ModelSerializer):
    # ServersSerializer()
    class Meta:
        model = ServerMenuCategory
        fields = "__all__"


class ServersSerializer(serializers.ModelSerializer):
    # implement = ChoiceDisplayField(choices=Servers.IMPLEMENT)
    category = ServerMenuCategorySerializer(read_only=True)

    # category_name = serializers.ReadOnlyField(source="category.name")
    class Meta:
        model = Servers
        fields = "__all__"


class PagesSerializer(serializers.ModelSerializer):
    # server = ServersSerializer(read_only=True)
    server_name = serializers.ReadOnlyField(source="server.name")
    category_name = serializers.ReadOnlyField(source="server.category.name")

    class Meta:
        model = Pages
        fields = "__all__"


class buttonsSerializer(serializers.ModelSerializer):
    # page = PagesSerializer(read_only=True)
    page_name = serializers.ReadOnlyField(source="page.name")
    server_name = serializers.ReadOnlyField(source="page.server.name")
    category_name = serializers.ReadOnlyField(source="page.server.category.name")

    class Meta:
        model = Button
        fields = "__all__"


class ServerMapWfSerializer(serializers.ModelSerializer):
    # category_code = serializers.CharField(max_length=100, read_only=True)
    # server_code = serializers.CharField(max_length=100, read_only=True)
    # page_code = serializers.CharField(max_length=100, read_only=True)
    process = serializers.SerializerMethodField()
    server_name = serializers.SerializerMethodField()
    node_name = serializers.SerializerMethodField()
    page_name = serializers.SerializerMethodField()

    def get_process(self, obj):
        return ProcessDefinition.objects.filter(id=obj.work_flow_key).values()

    def get_server_name(self, obj):
        # 取对象-key-values
        req = Servers.objects.filter(id=obj.server_id).values('name')
        if req:
            return req[0].get('name')

    def get_node_name(self, obj):
        req = TaskDefinition.objects.filter(id=obj.node_id).values('taskName__taskName')
        if req:
            return req[0].get("taskName__taskName")
        # return req if req else []

    def get_page_name(self, obj):
        req = Pages.objects.filter(id=obj.page_id).values('name')
        if req:
            return req[0].get('name')

    class Meta:
        model = ServerMapWf
        fields = "__all__"


class ServerMapBpSerializer(serializers.ModelSerializer):
    blue_print_name = serializers.SerializerMethodField()
    button_name = serializers.SerializerMethodField()

    def get_blue_print_name(self, obj):
        req = BluePrintDefinition.objects.filter(id=obj.blue_print_id).values('name')
        if req:
            return req[0].get('name')

    def get_button_name(self, obj):
        req = Button.objects.filter(id=obj.button_id).values('name')
        if req:
            return req[0].get('name')

    class Meta:
        model = ServerMapBp
        fields = "__all__"


class ServerParamsSerializer(serializers.ModelSerializer):
    # server_name = serializers.CharField(source="server.name", read_only=True)
    value_list = serializers.SerializerMethodField()
    # CH_SETTING_TYPES = serializers.ReadOnlyField(source="CH_SETTING_TYPE")
    # CH_INTERFACE_TYPES = serializers.ReadOnlyField(source="CH_INTERFACE_TYPE")
    # PARAMS_PURPOSE_TYPES = serializers.ReadOnlyField(source="PARAMS_PURPOSE_TYPE")
    server_name = serializers.SerializerMethodField()

    def get_value_list(self, obj):
        values_set = ServerParamValues.objects.filter(param_id=obj.id).all()
        if not values_set:
            return []
        values_list = []
        for i in values_set:
            format_str = "%s_%s" % (i.param_value_name, i.param_value_tag_name)
            values_list.append(format_str)
        return values_list

    def get_server_name(self, obj):
        req = Servers.objects.filter(id=obj.server_id).values('name')
        if req:
            return req[0].get('name')

    # category_Name = serializers.CharField(source="pDefinitionId.pCategoryKey.processCategoryName", read_only=True)
    class Meta:
        model = ServerParams
        fields = "__all__"


class ServerParamValuesSerializer(serializers.ModelSerializer):
    params_name_display = serializers.SerializerMethodField()
    param_name = serializers.SerializerMethodField()

    #
    def get_params_name_display(self, obj):
        #
        req = ServerParams.objects.filter(id=obj.param_id).values('params_name_display')
        if req:
            return req[0].get('params_name_display')

    def get_param_name(self, obj):
        #
        req = ServerParams.objects.filter(id=obj.param_id).values('params_name')
        if req:
            return req[0].get('params_name')

    class Meta:
        model = ServerParamValues
        fields = "__all__"


from django.forms.models import model_to_dict


class PrimaryApplicationSerializer(serializers.ModelSerializer):
    # server = ServersSerializer(read_only=True)
    secondary_app_list = serializers.SerializerMethodField()

    def get_secondary_app_list(self, obj):
        req_set = SecondaryApplication.objects.filter(parent_app=obj).all()
        if req_set:
            list1 = []
            for i in req_set:
                if i:
                    j = model_to_dict(i)
                    list1.append(j)
            if list1:
                return list1

    class Meta:
        model = PrimaryApplication
        fields = "__all__"


class SecondaryApplicationSerializer(serializers.ModelSerializer):
    # server = ServersSerializer(read_only=True)
    parent_app_name = serializers.ReadOnlyField(source="parent_app.app_name")
    parent_app_sort_name = serializers.ReadOnlyField(source="parent_app.app_short_name")

    class Meta:
        model = SecondaryApplication
        fields = "__all__"


class ServerMatchingRuleSerializer(serializers.ModelSerializer):
    # server = ServersSerializer(read_only=True)
    # parent_app_name = serializers.ReadOnlyField(source="parent_app.app_name")
    matched_condition = serializers.SerializerMethodField()
    param_values_name = serializers.SerializerMethodField()
    param_name = serializers.SerializerMethodField()

    # param_value = serializers.SerializerMethodField()

    def get_matched_condition(self, obj):
        # req = MatchedCondition.objects.filter(matching_rule=obj.id).values('matching_param__params_name_display')
        ins = ServerMatchingRule.objects.filter(id=obj.id).first()
        condition_set = ins.matched_condition.all()
        if condition_set:
            list2 = []
            for i in condition_set:
                dict1 = {}
                dict1['matching_param_name'] = i.matching_param.params_name_display
                req = ServerParamValues.objects.filter(id=i.matching_param_value_id).values('param_value_name')
                if req:
                    dict1['matching_param_value_name'] = req[0].get('param_value_name')
                list2.append(dict1)
            if list2:
                return list2

    def get_param_values_name(self, obj):
        list1 = []
        if type(obj.param_value_id) != list:
            p = re.compile(r'\d+(,\d+)*')
            l = []
            for m in p.finditer(obj.param_value_id):
                num_str = m.group()
                num_str_list = num_str.split(",")
                for i in num_str_list:
                    i_int = int(i)
                    l.append(i_int)
            for i in l:
                param_value_ins = ServerParamValues.objects.filter(id=i).first()
                if param_value_ins:
                    list1.append(param_value_ins.param_value_name)
            # print list1 ,type(list1)
            if list1:
                return list1
        elif type(obj.param_value_id) == list:
            for i in obj.param_value_id:
                param_value_ins = ServerParamValues.objects.filter(id=int(i)).first()
                if param_value_ins:
                    list1.append(param_value_ins.param_value_name)
            # print list1 ,type(list1)
            if list1:
                return list1
        # elif not obj.param_value_id:
        #     return []
    def get_param_name(self, obj):
        req = ServerParams.objects.filter(id=obj.param_id).values('params_name_display')
        if req:
            return req[0].get('params_name_display')

    # def get_param_value(self, obj):
    #     list1 = []
    #     for i in obj.param_value_id:
    #
    #         req = ServerParamValues.objects.filter(id=i).values('param_value_name')
    #         if req:
    #             list1.append(req[0].get('param_value_name'))
    #     if list1:
    #         return list1

    class Meta:
        model = ServerMatchingRule
        fields = "__all__"


class MatchedConditionSerializer(serializers.ModelSerializer):
    matching_param_name = serializers.ReadOnlyField(source="matching_param.params_name_display")
    # def get_matching_param_name(self,obj):
    #     return MatchedCondition.objects.filter(id =obj.matching_param. )
    # matching_rule_info = serializers.SerializerMethodField()
    matching_param_value = serializers.SerializerMethodField()

    def get_matching_param_value(self, obj):
        req = ServerParamValues.objects.filter(id=obj.matching_param_value_id).values('param_value_name')
        if req:
            return req[0].get('param_value_name')

    # def get_matching_rule_info(self,obj):
    #     pass
    class Meta:
        model = MatchedCondition
        fields = "__all__"
