from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name="login"),
    path('register/', views.register, name='register'),

    path('search/',views.search_rooms, name='search_rooms'),

    path('get-districts/<int:province_id>/',views.get_districts,name='get_districts'),
]