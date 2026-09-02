from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('iad/', views.test_response, name='iad'),
    path('kixie/test', views.test_post, name='webhook_test'),
    path('kixie/dial-attempt', views.dial_attempt_webhook, name='webhook_dial_attempt'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Management (staff only)
    path('manage/', views.manage_home, name='manage_home'),
    path('manage/customer/new/', views.manage_customer_new, name='manage_customer_new'),
    path('manage/customer/<int:customer_id>/', views.manage_customer_detail, name='manage_customer_detail'),
    path('manage/customer/<int:customer_id>/powerlist/add/', views.manage_powerlist_add, name='manage_powerlist_add'),
    path('manage/customer/<int:customer_id>/powerlist/<int:cp_id>/delete/', views.manage_powerlist_delete, name='manage_powerlist_delete'),
    path('manage/customer/<int:customer_id>/user/new/', views.manage_user_new, name='manage_user_new'),
    path('manage/customer/<int:customer_id>/user/<int:user_id>/reset-password/', views.manage_user_reset_password, name='manage_user_reset_password'),
    path('manage/customer/<int:customer_id>/user/<int:user_id>/delete/', views.manage_user_delete, name='manage_user_delete'),
]

