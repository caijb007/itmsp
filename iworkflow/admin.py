# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from iworkflow import models
from business import models as b_model

admin.site.register(b_model.WorkflowAndBusiness)
admin.site.register(b_model.WorkflowLog)
for table in models.__all__:
    admin.site.register(getattr(models, table))

# Register your models here.
