# coding:utf-8
# Author: Chery-Huo
# description: 序列化模型字段
from rest_framework import serializers

from iworkflow import models


# class ProcessCategorySerializer(serializers.ModelSerializer):
class ProcessCategorySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='processcategory-detail', lookup_field='pk')
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    updateTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = models.ProcessCategory
        fields = ('url', 'id', 'processCategoryName', 'processCategoryKey', 'createTime', 'updateTime')


class ProcessDefinitionSerializer(serializers.HyperlinkedModelSerializer):
    # category_name = serializers.CharField(source="pCategoryKey.processCategoryName")
    url = serializers.HyperlinkedIdentityField(view_name='processdefinition-detail', lookup_field='pk')
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    updateTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    category_name = serializers.ReadOnlyField(source="pCategoryKey.processCategoryName")
    category_id = serializers.IntegerField(source="pCategoryKey.pk", read_only=True)

    class Meta:
        model = models.ProcessDefinition
        # fields = "__all__"
        fields = ('url',
                  'id',
                  'category_id',
                  'processDefinitionName',
                  'processDefinitionKey',
                  'processNodes',
                  'is_deleted',
                  'createTime',
                  'updateTime',
                  'category_name',
                  'pCategoryKey'
                  )
        # exclude = ('pCategoryKey',)


#

class ProcessTaskNodeSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tasknode-detail', lookup_field='pk')
    category_name = serializers.ReadOnlyField(source="pCategoryKey.processCategoryName")
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    updateTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = models.TaskNode
        # fields = '__all__'
        fields = ('url', 'id', 'taskName', 'category_name', 'createTime', 'updateTime', 'pCategoryKey')

from iuser.models import  ExUser
class ProcessTaskDefinitionSerializer(serializers.ModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='taskdefinition-detail', lookup_field='pk')
    # processDefinitionId = serializers.IntegerField(source='models.ProcessDefinition.processDefinitionId')
    # processDefinitionId = serializers.ReadOnlyField()
    processDefinition_Name = serializers.ReadOnlyField(source="pDefinitionId.processDefinitionName")
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    # endTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    task_Name = serializers.CharField(source="taskName.taskName", read_only=True)
    processDefinition_id = serializers.IntegerField(source="pDefinitionId.pk", read_only=True)
    candidate = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ExUser.objects.all(),
        many=True
        # read_only=True
    )
    # candidate_name = serializers.CharField(source="candidate.")
    # candidate_set = serializers.CharField(source="candidate",read_only=True)
    # candidate_list = serializers.JSONField(default=[], allow_null=True)

    # l1 = []
    # for candidate_obj in l:
    #     l1.append(candidate_obj)
    #
    # candidate_id = serializers.ReadOnlyField(source=l1)

    class Meta:
        model = models.TaskDefinition
        # fields = '__all__'
        fields = (
            'id', 'processDefinition_Name', 'candidate', 'taskName', 'taskNode', 'createTime', 'pDefinitionId',
            'task_Name',
            'processDefinition_id')


from iuser import models as i_models


class ProcessInstanceSerializer(serializers.ModelSerializer):
    processDefinition_Name = serializers.CharField(source="pDefinitionId.processDefinitionName", read_only=True)
    category_Name = serializers.CharField(source="pDefinitionId.pCategoryKey.processCategoryName", read_only=True)
    # business_name = serializers.CharField(source="businessKey.title",read_only=True)
    currentProcessNode_name = serializers.CharField(source="currentProcessNode.taskName", read_only=True)
    startTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    endTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    # currentProcessNode_examiner = ProcessTaskDefinitionSerializer()
    currentProcessNode = ProcessTaskDefinitionSerializer()
    # currentProcessNode_c = serializers.CharField(source="currentProcessNode.candidate.all.", read_only=True)
    # ss = currentProcessNode.data
    #     CharField
    class Meta:
        model = models.ProcessInstance
        fields = ('id', 'pDefinitionId', 'instance_name', 'category_Name', 'businessKey', 'startTime',
                  'endTime', 'duration', 'startUserID',
                  'currentProcessNode', 'processStatus',
                  'processDefinition_Name',
                  'instance_name',
                  'currentProcessNode_name',
                  # 'currentProcessNode_c'
                  # 'currentProcessNode_examiner'
                  )
        # fields = "__all__"


class TaskInstanceSerializer(serializers.HyperlinkedModelSerializer):
    processDefinition_Name = serializers.CharField(source="pDefinitionId.processDefinitionName", read_only=True)
    taskDefinition_Name = serializers.CharField(source="tDefinitionId.taskName", read_only=True)
    taskNodeName = serializers.CharField(source="taskNode.taskName", read_only=True)
    startTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    endTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = models.TaskInstance
        fields = ('url', 'id', 'taskName', 'processDefinition_Name',
                  'taskDefinition_Name', 'taskNodeName', 'pInstanceId',
                  'pDefinitionId', 'businessKey', 'tDefinitionId',
                  'taskNode', 'startTime','assignee',
                  'endTime', 'duration', 'taskStatus',
                  'comment',)


# class ProcessConfigSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.ProcessConfig
#         fields = "__all__"

class BusinessToProcessSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='businesstoprocess-detail', lookup_field='pk')

    class Meta:
        model = models.BusinessToProcess
        fields = ('url', 'id', 'business', 'tables')
