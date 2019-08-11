# coding: utf-8
# Author: ld

from django.conf.urls import url, include
from . import views
from rest_framework.routers import DefaultRouter
# from iconfig.tasks import BLueEngine
from iconfig.blue_engine.blue_engine import BLueEngine
router = DefaultRouter()
# 组件抽象
router.register(r'blue-component-def', views.BlueComponentDefinitionViewSet)

# 组件分组
router.register(r'blue-component-cate', views.BlueComponentCategoryViewSet)
router.register(r'blue-interface-cate', views.BlueInterfaceCategoryViewSet)
router.register(r'blue-pre-param-group-cate', views.BluePreParamGroupCategoryViewSet)
router.register(r'blue-acc-module-param-group-cate', views.BlueAccessModuleParamGroupCategoryViewSet)
router.register(r'blue-cate', views.BlueCategoryViewSet)

# 组件实体
# router.register(r'blue-component-entity', views.BlueComponentEntityDefinitionViewSet)
router.register(r'blue-interface-def', views.BlueInterfaceDefinitionViewSet)
router.register(r'blue-pre-param-group', views.BluePreParamGroupViewSet)
router.register(r'blue-acc-module-param-group', views.BlueAccessModuleParamGroupViewSet)
router.register(r'blue-print-def', views.BluePrintDefinitionViewSet)

# 组件实体参数
router.register(r'blue-interface-param', views.BlueInterfaceParamViewSet)
router.register(r'blue-pre-param-group-param', views.BluePreParamGroupParamViewSet)
router.register(r'blue-acc-module-param-group-param', views.BlueAccessModuleParamsGroupParamViewSet)

# 节点
router.register(r'blue-node-def', views.BlueNodeDefinitionViewSet)
router.register(r'blue-node-map-param', views.BlueNodeMapParamViewSet)

# 引擎
router.register(r'blue-instance', views.BlueInstanceViewSet)
router.register(r'node-instance', views.NodeInstanceViewSet)
router.register(r'blue-acc-module-param-ins', views.BlueAccessModuleParamsInstanceViewSet)
router.register(r'blue-engine-task', views.BlueEngineTaskViewSet)

# from iconfig.blue_engine.blue_engine import BLueEngine

# b = BLueEngine()
urlpatterns = [
    # url(r'', include(router.urls)),
    url(r"blue-engine-query", BLueEngine.blue_engine_query),
    url(r"blue-engine-instance", BLueEngine.blue_engine_instance),
    url(r"blue-engine-restart", BLueEngine.blue_engine_task_restart),
    url(r"blue-engine-recover", BLueEngine.blue_engine_task_recover),
]
urlpatterns += router.urls
