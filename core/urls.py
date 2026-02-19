from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('iad/', views.test_response, name='iad'),
]
