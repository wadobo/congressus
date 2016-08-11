from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^gen/(?P<ev>[\w-]+)/$', views.gen_invitations, name='gen_invitations'),
]


