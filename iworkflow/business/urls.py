# coding:utf-8
# Author: Chery-Huo
from iworkflow.business import views
from rest_framework.routers import DefaultRouter

# init router
router = DefaultRouter()

# router.register(r'businfo', views.BusinessInfoModeView)

urlpatterns = [
    # url(r'^pcategory/',include([
    # url(r'^list/$', views.workflow_list),
    # url(r'^list/$', views.ProcessCategoryView.as_view()),
    # url(r'^workflowCategory/$', views.workflowCategory)
    # url(r'^add/$', views.workflow_add)
    # url(r'^edit/$', views.workflow_add)
]
# )
# )

# ]
urlpatterns += router.urls
