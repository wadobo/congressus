from django.urls import path
from . import views


urlpatterns = [
    path('<str:ev>/list/', views.dlist, name='dashboard_list'),
    path('<str:ev>/<str:dash>/', views.general, name='dashboard_general'),
]
