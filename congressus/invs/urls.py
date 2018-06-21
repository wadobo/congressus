from django.urls import path
from . import views


urlpatterns = [
    path('gen/<str:ev>/', views.gen_invitations, name='gen_invitations'),
]
