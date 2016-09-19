from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^(?P<ev>[\w-]+)/$', views.report, name='report'),
]

