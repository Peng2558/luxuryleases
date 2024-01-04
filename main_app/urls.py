from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/signup/', views.signup, name='signup'),
    path('about/', views.about, name='about'),
    path('cars/',views.cars_index, name='cars_index'),
    path('rentals/new', views.rentals_new,name='rentals_new'),
    path('rentals/create', views.rentals_create, name='rentals_create'),
    path('stores/',views.stores_index, name='stores_index'),
    path('stores/select/<int:store_id>/', views.select_store, name='select_store'),
    

]
