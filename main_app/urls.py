from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/signup/', views.signup, name='signup'),
    path('about/', views.about, name='about'),
    path('cars/',views.cars_index, name='cars_index'),
    path('rentals/new', views.rentals_new,name='rentals_new'),
    path('rentals/create', views.rentals_create, name='rentals_create'),
    path('rentals/<int:rental_id>', views.rental_detail, name='rental_detail'),
    path('rentals/<int:rental_id>/update', views.rental_update, name='rental_update'),
    path('rentals/<int:pk>/delete', views.RentalDelete.as_view(), name='rental_delete'),
    path('stores/', views.stores_index, name='stores_index'),
    path('stores/select/<int:store_id>/', views.select_store, name='select_store'),
    path('users/<int:user_id>/', views.users_detail, name='users_detail'),
    path('administrator/', views.admin_page,name='admin'),
    path('administrator/photo/', views.add_photo, name='add_photo'),
    
   
    

]
