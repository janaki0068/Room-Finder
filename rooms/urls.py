from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name="login"),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('search/',views.search_rooms, name='search_rooms'),

    path('saved/', views.saved_view, name='saved_view'),
    path('list/', views.list_view, name='list_view'),
    path('profile/', views.profile_view, name='profile_view'),
]