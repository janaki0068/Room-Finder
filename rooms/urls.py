from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name="login"),

    path('register/', views.register_view, name='register'),


    path('logout/', views.logout_view, name='logout'),

    path('search/', views.search_rooms, name='search_rooms'),

    path('get-districts/<int:province_id>/',
         views.get_districts, name='get_districts'),
    path('saved/', views.saved_view, name='saved_view'),
    path('list/', views.list_view, name='list_view'),
    path('profile/', views.profile_view, name='profile_view'),

    path("landlord-dashboard/", views.landlord_dashboard,
         name="landlord_dashboard"),
    path("my-listings/", views.my_listings, name="my_listings"),
    path("saved-rooms/", views.saved_rooms, name="saved_rooms"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("upload-listing/", views.upload_listing, name="upload_listing"),
    path("messages/", views.messages_view, name="messages"),
    path("settings/", views.settings_view, name="settings"),

    path('get-districts/<int:province_id>/',
         views.get_districts, name='get_districts'),

    path("tenant-dashboard/", views.tenant_dashboard, name="tenant_dashboard"),

]
