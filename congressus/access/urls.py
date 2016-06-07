from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^(?P<ev>[\w-]+)/(?P<ac>[\w-]+)/logout/$', views.access_logout, name='access_logout'),
    url(r'^(?P<ev>[\w-]+)/(?P<ac>[\w-]+)/login/$', views.access_login, name='access_login'),
    url(r'^(?P<ev>[\w-]+)/(?P<ac>[\w-]+)/$', views.access, name='access'),
]

