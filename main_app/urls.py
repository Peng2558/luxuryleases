from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/signup/', views.signup, name='signup'),
    path('about/', views.about, name='about'),
    path('cars/',views.cars_index, name='cars_index'),
    path('rentals/create', views.rentals_create,name='rentals_create')


]
