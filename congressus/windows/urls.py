from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^(?P<ev>[\w-]+)/$', views.window_list, name='window_list'),
    url(r'^(?P<ev>[\w-]+)/(?P<w>[\w-]+)/logout/$', views.window_logout, name='window_logout'),
    url(r'^(?P<ev>[\w-]+)/(?P<w>[\w-]+)/login/$', views.window_login, name='window_login'),
    url(r'^(?P<ev>[\w-]+)/(?P<w>[\w-]+)/$', views.window_multipurchase, name='window_multipurchase'),
    url(r'^(?P<ev>[\w-]+)/(?P<w>[\w-]+)/(?P<pf>[\w-]+)/(?P<order>[\w-]+)/$', views.window_ticket, name='window_ticket'),
]

