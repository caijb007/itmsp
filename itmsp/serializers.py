# coding: utf-8
# Author: Dunkle Qiu

from rest_framework import serializers
from .models import *
from collections import OrderedDict


class ChoiceDisplayField(serializers.Field):
    """Custom ChoiceField serializer field"""

    def __init__(self, choices, **kwargs):
        self._choices = OrderedDict(choices)
        super(ChoiceDisplayField, self).__init__(**kwargs)

    def to_representation(self, value):
        return self._choices[value]

    def to_internal_value(self, data):
        for i in self._choices:
            if i == data or self._choices[i] == data:
                return i
        raise serializers.ValidationError("Acceptable values are {0}.".format(list(self._choices.values())))


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = ('id', 'name', 'full_name', 'primary_dev', 'app_level', 'dr_level')


class SystemSerializerDetail(serializers.ModelSerializer):
    other_dev = serializers.JSONField()
    other_op = serializers.JSONField()

    class Meta:
        model = System
        fields = ('id', 'name', 'full_name', 'app_level', 'dr_level', 'topo_graph',
                  'primary_dev', 'other_dev', 'primary_op', 'other_op')


class J2TemplFileSerializer(serializers.ModelSerializer):
    var_dict = serializers.JSONField()

    class Meta:
        model = J2TemplFile
        fields = ('id', 'src', 'dest', 'host', 'owner', 'group',
                  'mode', 'var_dict')


class DataDictSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDict
        fields = '__all__'
