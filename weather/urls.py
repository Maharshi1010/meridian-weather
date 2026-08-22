from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.home, name='home'),
    path('favorites/add/', views.add_favorite, name='add_favorite'),
    path('favorites/<int:favorite_id>/remove/', views.remove_favorite, name='remove_favorite'),
]
