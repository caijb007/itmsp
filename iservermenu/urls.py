# coding: utf-8
# Author: ld

from django.conf.urls import include, url
from . import views
from blueprint_to_workflow.blueprint_and_workflow_mq import bwmq_api,restart_bw_mq
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'server-menu-cate', views.ServerMenuCategoryViewSet)
router.register(r'server', views.ServersViewSet)
router.register(r'page', views.PagesViewSet)
router.register(r'button', views.buttonsViewSet)
router.register(r'server-map-wf', views.ServerMapWfViewSet)
router.register(r'server-map-bp', views.ServerMapBpViewSet)
router.register(r'server-params', views.ServerParamsViewSet)
router.register(r'server-params_value', views.ServerParamValuesViewSet)
router.register(r'primary_application', views.PrimaryApplicationViewSet)
router.register(r'secondary_application', views.SecondaryApplicationViewSet)
router.register(r'server-param-matching', views.ServerMatchingRuleViewSet)
router.register(r'server-param-matching-condition', views.MatchedConditionViewSet)

urlpatterns = [
    # url(r'', include(router.urls))
    url(r'get-code/$', views.get_code),
    url(r'get-bw-mq/$', bwmq_api),
    url(r'restart-bw-mq/$', restart_bw_mq)
]

urlpatterns +=router.urls