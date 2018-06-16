from django.urls import path
from . import views


app_name = 'invs'

urlpatterns = [
    path('gen/<str:ev>/', views.gen_invitations, name='gen_invitations'),
]
