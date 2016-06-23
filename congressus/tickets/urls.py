from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^event/(?P<ev>[\w-]+)/$', views.event, name='event'),

    url(r'^event/(?P<ev>[\w-]+)/(?P<space>[\w-]+)/(?P<session>[\w-]+)/register/$', views.register, name='register'),
    url(r'^ticket/(?P<order>[\w-]+)/payment/$', views.payment, name='payment'),
    url(r'^ticket/(?P<order>[\w-]+)/thanks/$', views.thanks, name='thanks'),
    url(r'^ticket/confirm/$', views.confirm, name='confirm'),

    url(r'^generator/invitations/$', views.gen_invitations, name='gen_invitations'),
    url(r'^generator/passes/$', views.gen_passes, name='gen_passes'),
    url(r'^generator/get-types/$', views.get_types, name='get_types'),

    url(r'^(?P<ev>[\w-]+)/$', views.multipurchase, name='multipurchase'),

    url(r'^seats/(?P<session>\d+)/(?P<layout>\d+)/$', views.ajax_layout, name='ajax_layout'),
    url(r'^seats/view/(?P<map>\d+)/$', views.seats, name='seats'),
    url(r'^seats/auto/$', views.autoseats, name='autoseats'),
]

