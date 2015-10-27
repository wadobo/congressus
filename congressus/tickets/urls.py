from django.conf.urls import url


urlpatterns = [
    url(r'^event/(?P<evid>\d+)/register/', 'tickets.views.register', name='register'),
    url(r'^ticket/(?P<tkid>\d+)/payment/', 'tickets.views.payment', name='payment'),
]

