from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('pending/', views.pending_listings, name='pending_listings'),
    path('active/', views.active_listings, name='active_listings'),
    path('rented/', views.rented_listings, name='rented_listings'),
    path('rejected/', views.rejected_listings, name='rejected_listings'),

    path('approve/<int:room_id>/', views.approve_listing, name='approve_listing'),
    path('reject/<int:room_id>/', views.reject_listing, name='reject_listing'),

    path('users/', views.user_management, name='user_management'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    path('logout/', views.custom_logout, name='logout'),

    path('ads/', views.ad_list, name='ad_list'),
    path('ads/new/', views.ad_create, name='ad_create'),
    path('ads/<int:ad_id>/edit/', views.ad_edit, name='ad_edit'),
    path('ads/<int:ad_id>/toggle/', views.ad_toggle, name='ad_toggle'),
    path('ads/<int:ad_id>/delete/', views.ad_delete, name='ad_delete'),
]