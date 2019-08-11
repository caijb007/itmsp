"""itmsp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^options/', include([
        url(r'^apps/$', views.option_apps),
        url(r'^names/$', views.option_names),
        url(r'^add/$', views.option_add),
        url(r'^list/$', views.option_list),
        url(r'^edit/$', views.option_edit),
        url(r'^delete/$', views.option_delete),
    ])),
    url(r'^iuser/', include('iuser.urls')),
    url(r'^iworkflow/', include('iworkflow.urls')),
    url(r'^ivmware/', include('ivmware.urls')),
    url(r'^iconfig/', include('iconfig.urls')),
    url(r'^icatalog/', include('iservermenu.urls')),
    url(r'^api-token-auth/', views.ObtainExAuthToken.as_view()),

]
