# coding: utf-8
# Author: ld

from rest_framework import serializers
from iuser.models import ExUser
from .models import *
from collections import OrderedDict
from itmsp.serializers import ChoiceDisplayField


class BlueComponentDefinitionSerializer(serializers.ModelSerializer):
    component_type = ChoiceDisplayField(choices=COMPONENT_TYPE)

    class Meta:
        model = BlueComponentDefinition
        fields = '__all__'


class BlueComponentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueComponentCategory
        fields = '__all__'


class BlueComponentEntityDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueComponentEntityDefinition
        fields = '__all__'


class BlueInterfaceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueInterfaceCategory
        fields = '__all__'


class BluePreParamGroupCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BluePreParamGroupCategory
        fields = '__all__'


class BlueAccessModuleParamGroupCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueAccessModuleParamGroupCategory
        fields = '__all__'


class BlueCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueCategory
        fields = '__all__'


class BlueInterfaceParamSerializer(serializers.ModelSerializer):
    io_stream = ChoiceDisplayField(choices=STREAM_TYPE)
    data_type = ChoiceDisplayField(choices=DATA_TYPE)

    class Meta:
        model = BlueInterfaceParam
        fields = '__all__'


class BlueInterfaceDefinitionSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=BlueInterfaceCategory.objects.all()
    )
    color = serializers.StringRelatedField(
        source='category.color'
    )
    component_type = serializers.IntegerField(default=0, read_only=True)

    class Meta:
        model = BlueInterfaceDefinition
        fields = '__all__'


class BluePreParamGroupParamSerializer(serializers.ModelSerializer):
    data_type = ChoiceDisplayField(choices=DATA_TYPE)

    class Meta:
        model = BluePreParamGroupParam
        fields = '__all__'


class BluePreParamGroupSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=BluePreParamGroupCategory.objects.all()
    )
    color = serializers.StringRelatedField(
        source='category.color'
    )
    component_type = serializers.IntegerField(default=1, read_only=True)

    class Meta:
        model = BluePreParamGroup
        fields = '__all__'


class BlueAccessModuleParamsGroupParamSerializer(serializers.ModelSerializer):
    data_type = ChoiceDisplayField(choices=DATA_TYPE)

    class Meta:
        model = BlueAccessModuleParamsGroupParam
        fields = '__all__'


class BlueAccessModuleParamGroupSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=BlueAccessModuleParamGroupCategory.objects.all()
    )
    color = serializers.StringRelatedField(
        source='category.color'
    )
    component_type = serializers.IntegerField(default=2, read_only=True)

    class Meta:
        model = BlueAccessModuleParamGroup
        fields = '__all__'


class BlueNodeDefinitionSerializer(serializers.ModelSerializer):
    component_data = serializers.JSONField(default={})
    component_type = ChoiceDisplayField(choices=COMPONENT_TYPE, default=0)

    class Meta:
        model = BlueNodeDefinition
        fields = '__all__'


class BluePrintDefinitionSerializer(serializers.ModelSerializer):
    keep_status = ChoiceDisplayField(choices=BluePrintDefinition.KEEP_STATUS, read_only=True)
    is_valid = ChoiceDisplayField(choices=BluePrintDefinition.VALID_STATUS, default=0)
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=BlueCategory.objects.all()
    )
    created_user = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ExUser.objects.all()
    )
    name = serializers.CharField(default='未命名')
    link_data = serializers.JSONField(default={})
    avaliable_node_sort = serializers.JSONField(default=[])
    blue_nodes = BlueNodeDefinitionSerializer(many=True, read_only=True)

    class Meta:
        model = BluePrintDefinition
        fields = '__all__'


class BlueNodeMapParamSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueNodeMapParam
        fields = '__all__'


class NodeInstanceSerializer(serializers.ModelSerializer):
    startTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    endTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)

    class Meta:
        model = NodeInstance
        fields = "__all__"


class BlueInstanceSerializer(serializers.ModelSerializer):
    startTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    endTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    avaliable_node_sort = serializers.JSONField(default=[])
    status = serializers.ChoiceField(
        choices=BlueInstance.STATUS,
        default=0,
        source="get_status_display",
        read_only=True
    )
    user = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ExUser.objects.all()
    )

    # access_module_key = serializers.ReadOnlyField(source="BlueEngineTask.access_module_key")

    class Meta:
        model = BlueInstance
        fields = "__all__"


class BlueAccessModuleParamsInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueAccessModuleParamsInstance
        fields = '__all__'


class BlueEngineTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueEngineTask
        fields = '__all__'
