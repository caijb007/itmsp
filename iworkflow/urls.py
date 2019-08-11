# coding:utf-8
# Author: Chery-Huo
from iworkflow.workflow import views
from rest_framework.routers import DefaultRouter

from business.views import WorkflowAndBusinessModelView
from django.conf.urls import url,include
# init router
router = DefaultRouter()

router.register(r'pcategory', views.ProcessCategoryModelView)
router.register(r'pdefinition', views.ProcessDefinitionModelView)
router.register(r'ptasknode', views.ProcessTaskNodeModelView)
router.register(r'ptaskdef', views.TaskDefinitionModelView)
router.register(r'pinstance', views.ProcessInstanceModelView)
router.register(r'taskinstance', views.TaskInstanceModelView)
# router.register(r'btp', views.BusinessToProcessModelView)
# router.register(r'workflow_business', WorkflowAndBusinessModelView)
urlpatterns = [

    url(r'api/process-detail/(?P<pk>[^/.]+)/$',views.look_look_process_detail),

    url(r'api/node-show/(?P<pk>[^/.]+)/$',views.node_step_show),

]

urlpatterns += router.urls
