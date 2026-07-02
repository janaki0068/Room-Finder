from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name="login"),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_rooms, name='search_rooms'),
    path('get-districts/<int:province_id>/',
         views.get_districts, name='get_districts'),

    # LANDLORD -->
    path("landlord-dashboard/", views.landlord_dashboard,
         name="landlord_dashboard"),
    path("upload-listing/", views.upload_listing, name="upload_listing"),
    path("my-listings/", views.my_listings, name="my_listings"),
    path('room/<int:room_id>/', views.room_detail, name="room_detail"),
    path('edit-listing/<int:room_id>/', views.edit_listing, name="edit_listing"),
    path('delete-listing/<int:room_id>/',
         views.delete_listing, name="delete_listing"),
    path("saved-rooms/", views.saved_rooms, name="saved_rooms"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("messages/", views.messages_view, name="messages"),
    path("messages/<int:user_id>/<int:room_id>/",
         views.chat_room, name="chat_room"),
    path("settings/", views.settings_view, name="settings"),

    path('settings/password/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    

    # TENANT -->
    path("tenant-dashboard/", views.tenant_dashboard, name="tenant_dashboard"),
    path("tsearch/", views.tsearch_rooms, name="tsearch_rooms"),
    path('saved/', views.saved_view, name='saved_view'),
    path('unsave/<int:room_id>/', views.unsave_room, name='unsave_room'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.tenant_edit_profile, name='tenant_edit_profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('settings/', views.settings_view, name='settings_view'),
]
