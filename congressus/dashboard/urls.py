from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^(?P<ev>[\w-]+)/$', views.dlist, name='dashboard_list'),
    url(r'^(?P<ev>[\w-]+)/(?P<dash>[\w-]+)/$', views.general, name='dashboard_general'),
]
