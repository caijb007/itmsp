# coding: utf-8
# Author: Chery-Huo

from __future__ import unicode_literals
from . import serializers
from models import WorkflowAndBusiness

from rest_framework.viewsets import ModelViewSet


class WorkflowAndBusinessModelView(ModelViewSet):
    queryset = WorkflowAndBusiness.objects.all()
    serializer_class = serializers.WorkflowAndBusinessSerializer
