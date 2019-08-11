# coding: utf-8
# Author: Chery-Huo

from rest_framework import serializers
from . import models
from iworkflow.models import *


class WorkflowAndBusinessSerializer(serializers.ModelSerializer):
    process_category_name = serializers.ReadOnlyField(source="pCategory.processCategoryName")
    process_definition_name = serializers.ReadOnlyField(source="pDefinition.processDefinitionName")
    process_node_name = serializers.ReadOnlyField(source="pNode.taskName")
    definition_name = serializers.ReadOnlyField(source="taskDefinition.taskName.taskName")

    class Meta:
        model = models.WorkflowAndBusiness
        fields = "__all__"


class WorkflowLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowLog
        fields = "__all__"
