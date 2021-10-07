from django.urls import path
from invs import views


urlpatterns = [
    path('gen/<str:ev>/', views.gen_invitations, name='gen_invitations'),
]
