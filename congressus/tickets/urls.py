from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^event/(?P<ev>[\w-]+)/$', views.event, name='event'),

    url(r'^event/(?P<ev>[\w-]+)/(?P<space>[\w-]+)/(?P<session>[\w-]+)/register/$', views.register, name='register'),
    url(r'^ticket/(?P<order>[\w-]+)/payment/$', views.payment, name='payment'),
    url(r'^ticket/(?P<order>[\w-]+)/thanks/$', views.thanks, name='thanks'),
    url(r'^ticket/confirm/$', views.confirm, name='confirm'),

    url(r'^(?P<ev>[\w-]+)/$', views.multipurchase, name='multipurchase'),

    url(r'^seats/view/(?P<map>\d+)/$', views.seats, name='seats'),
]

