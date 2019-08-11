# coding:utf-8
# Author: Chery-Huo

from django import forms
from iworkflow import models


class ProcessCategoryForm(forms.ModelForm):
    class Meta:
        model = models.ProcessCategory
        fields = '__all__'
