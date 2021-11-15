from django.urls import path
from access import views


urlpatterns = [
    path('<str:ev>/', views.access_list, name='access_list'),
    path('<str:ev>/<str:ac>/logout/', views.access_logout, name='access_logout'),
    path('<str:ev>/<str:ac>/login/', views.access_login, name='access_login'),
    path('<str:ev>/<str:ac>/', views.access, name='access'),
]
