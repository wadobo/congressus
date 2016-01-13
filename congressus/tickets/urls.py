from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^event/(?P<evid>\d+)/register/', views.register, name='register'),
    url(r'^ticket/(?P<order>[\w-]+)/payment/', views.payment, name='payment'),
    url(r'^ticket/(?P<order>[\w-]+)/thanks/', views.thanks, name='thanks'),
    url(r'^ticket/confirm/', views.confirm, name='confirm'),
]

