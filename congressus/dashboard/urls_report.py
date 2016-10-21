from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^(?P<ev>[\w-]+)/$', views.report_list, name='report'),

    url(r'^(?P<ev>[\w-]+)/general/$', views.report_general, name='general_report'),
    url(r'^(?P<ev>[\w-]+)/window/$', views.report_window, name='window_report'),
    url(r'^(?P<ev>[\w-]+)/online/$', views.report_online, name='online_report'),
    url(r'^(?P<ev>[\w-]+)/count/$', views.report_count, name='count_report'),
]

