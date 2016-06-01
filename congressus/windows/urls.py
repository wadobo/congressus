from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^(?P<ev>[\w-]+)/(?P<w>[\w-]+)/$', views.window_login, name='window_login'),
]

