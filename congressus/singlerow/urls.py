from django.urls import path
from . import views


urlpatterns = [
    path('', views.singlerow, name='singlerow'),
    path('<str:ev>/', views.singlerow_view, name='singlerow_view'),
]
