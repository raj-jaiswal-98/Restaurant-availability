from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [
path('', views.getData),
path('trigger_report/', views.trigger_report),
path('get_report/', views.get_report),
]