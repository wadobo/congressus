from django.urls import path
from . import views


urlpatterns = [
    path('<str:ev>/', views.window_list, name='window_list'),
    path('<str:ev>/<str:w>/logout/', views.window_logout, name='window_logout'),
    path('<str:ev>/<str:w>/login/', views.window_login, name='window_login'),
    path('<str:ev>/<str:w>/', views.window_multipurchase, name='window_multipurchase'),
    path('<str:ev>/<str:w>/<str:pf>/<str:order>/', views.window_ticket, name='window_ticket'),
]

