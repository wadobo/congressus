from django.urls import path
from . import views


urlpatterns = [
    path('<str:ev>/', views.report_list, name='report'),

    path('<str:ev>/general/', views.report_general, name='general_report'),
    path('<str:ev>/window/', views.report_window, name='window_report'),
    path('<str:ev>/online/', views.report_online, name='online_report'),
    path('<str:ev>/count/', views.report_count, name='count_report'),
]
