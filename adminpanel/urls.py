from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('pending/', views.pending_listings, name='pending_listings'),
    path('approved/', views.approved_listings, name='approved_listings'),
    path('rejected/', views.rejected_listings, name='rejected_listings'),

    path('approve/<int:room_id>/', views.approve_listing, name='approve_listing'),
    path('reject/<int:room_id>/', views.reject_listing, name='reject_listing'),

    path('users/', views.user_management, name='user_management'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
]
