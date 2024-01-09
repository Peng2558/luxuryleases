import boto3
import datetime
import os
import uuid
from datetime import datetime, timedelta
from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.edit import DeleteView, CreateView, UpdateView
from .forms import StoreForm
from .models import Car, Store, Rental, CreditCard

base_rate = 139

def calc_rate(date1, date2):
    d = datetime(int(date1[0:4]),int(date1[5:7]), int(date1[8:10]))
    p = datetime(int(date2[0:4]),int(date2[5:7]), int(date2[8:10]))
    days = d - p
    days = days.days
    return days

#===== PUBLIC =====

def home(request):
    img_url = Car.objects.order_by('?').first().photo_url
    return render(request, 'home.html', {
        'img_url': img_url
    })


def about(request):
  return render(request, 'about.html')


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')


def signup(request):
    error_message = ''
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = request.POST['email']
            user.save()
            login(request, user)
            return redirect('home')
        else:
            error_message = 'Unable to sign up'
    form = SignUpForm()
    return render(request, 'registration/signup.html', {
        'form': form,
        'error_message': error_message
    })


#===== USERS =====

def users_login(request):
    user_id = request.user.id
    if user_id == 1:
        return redirect('admin')
    return redirect('users_detail', user_id=user_id)


@login_required
def users_detail(request, user_id):
    d = datetime.today()
    user = User.objects.get(id=user_id)
    upcoming_rentals = Rental.objects.filter(
        user=user,
        dropoff_date__gte=d
    ).order_by('pickup_date')
    past_rentals = Rental.objects.filter(
        user=user,
        dropoff_date__lt=d
    ).order_by('-pickup_date')
    rentals = Rental.objects.filter(user=user_id)
    return render(request, 'users/detail.html', {
        'rentals': rentals,
        'upcoming_rentals': upcoming_rentals,
        'past_rentals': past_rentals,
        'user': user
    })


#===== CARS =====

@login_required
def cars_index(request):
    cars = Car.objects.all()
    return render(request,'cars/index.html', {
        'cars': cars
    })


@login_required
def cars_detail(request, car_id):
    car = Car.objects.get(id=car_id)
    rentals = Rental.objects.filter(car_id=car_id).order_by('-pickup_date')
    return render(request, 'cars/detail.html', {
        'car': car,
        'rentals': rentals
    })


#===== STORES =====

@login_required
def stores_index(request):
    stores = Store.objects.all()
    return render(request,'stores/index.html', {
        'stores': stores,
        'mapbox_access_token': os.environ['MAPBOX_ACCESS_TOKEN']
    })


@login_required
def select_store(request, store_id):
    request.session['selected_store'] = Store.objects.get(id=store_id).name
    return redirect('cars_index')


#===== RENTALS =====

@login_required    
def rentals_new(request):
    stores = Store.objects.all()
    cars = Car.objects.all()
    return render(request, 'main_app/rental_form.html/', {
        'stores': stores,
        'cars': cars,
    })


@login_required
def rentals_create(request):
    days = calc_rate(request.POST['dropoff_date'], request.POST['pickup_date'])
    new_rental = Rental.objects.create(
        pickup_date=request.POST['pickup_date'],
        dropoff_date=request.POST['dropoff_date'],
        dropoff_location=Store.objects.get(id=request.POST['dropoff_location']),
        car=Car.objects.get(id=request.POST['car']),
        user=request.user,
        rental_fee=days*base_rate
    )
    new_rental.save()
    return redirect('users_detail', user_id=request.user.id)

@login_required
def rentals_car(request, car_id):
    car = Car.objects.get(id=car_id)
    request.session['selected_store'] = Store.objects.get(id=car.current_store_id).name
    request.session['selected_car'] = car.id
    return redirect('rentals_new')

@login_required
def rentals_detail(request, rental_id):
    rental = Rental.objects.get(id=rental_id)
    d = datetime.now()
    allow_edit_delete = rental.dropoff_date > d
    request.session['selected_store'] = Store.objects.get(
        id=rental.car.current_store.id
    ).name
    return render(request, 'rentals/detail.html', {
        'allow_edit_delete': allow_edit_delete,
        'rental': rental
    })


@login_required
def rentals_edit(request, rental_id):
    rental = Rental.objects.get(id=rental_id)
    stores = Store.objects.all()
    cars = Car.objects.all()
    return render(request, 'rentals/update.html', {
        'rental': rental,
        'stores': stores,
        'cars': cars
    })


@login_required
def rentals_update(request, rental_id):
    days = calc_rate(request.POST['dropoff_date'], request.POST['pickup_date'])
    rental = Rental.objects.get(id=rental_id)
    rental.car = Car.objects.get(id=request.POST['car'])
    rental.pickup_date = request.POST['pickup_date']
    rental.dropoff_date = request.POST['dropoff_date']
    rental.dropoff_location = Store.objects.get(
        id=request.POST['dropoff_location']
    )
    rental.rental_fee = days*base_rate
    rental.save()
    return redirect('rentals_detail', rental_id=rental_id)


class RentalDelete(LoginRequiredMixin, DeleteView):
    model = Rental
    success_url = '/'


#===== ADMIN =====

@staff_member_required
def admin_page(request):
   cars = Car.objects.all()
   stores = Store.objects.all()
   return render(request, 'admin.html', {
       'cars': cars,
       'stores':stores
   })

@staff_member_required
def add_car(request):
   
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        try:
            bucket = os.environ['S3_BUCKET']
            s3.upload_fileobj(photo_file, bucket, key)
            url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
           
            car = Car.objects.create(
                make = request.POST['make'],
                model = request.POST['model'],
                year = request.POST['year'],
                license_plate = request.POST['license_plate'],
                mileage = request.POST['mileage'],
                current_store = Store.objects.get(id=request.POST['current_store']),
                photo_url = url
            )        
            car.save()
        except Exception as e:
         print('An error occurred uploading file to S3')
         print(e)

    
    return redirect('admin')


@staff_member_required
def add_store(request):
    if request.method == 'POST':
        store_name = request.POST.get('store_name')
        store_address = request.POST.get('store_address')
        Store.objects.create(name=store_name, address=store_address)
        return redirect('/stores/')  
    return render(request, 'admin')

@staff_member_required
def edit_car(request,car_id):
   
     car =Car.objects.get(id=car_id)
     stores= Store.objects.all()
     return render(request, 'cars/update.html', {
       
         'car':car,
         'stores':stores  
        
    })

@staff_member_required
def update_car(request, car_id):
    car = Car.objects.get(id=car_id)
    if request.method == 'POST':
        car.make = request.POST.get('make')
        car.model = request.POST.get('model')  
        car.year = request.POST.get('year')   
        car.license_plate = request.POST.get('license_plate')
        car.mileage = request.POST.get('mileage') 
        current_store_id = request.POST.get('current_store')

        if current_store_id:
            car.current_store = Store.objects.get(id=current_store_id)
        
        car.save()
        return redirect('cars_detail', car_id=car.id) 



    
class CarDelete(LoginRequiredMixin,DeleteView):
    model = Car   
    success_url = '/'

@staff_member_required
def edit_store(request,store_id):
    store = Store.objects.get(id=store_id)  
    return render(request, 'stores/update.html', {      
         
         'store':store 
        
    }) 


@staff_member_required
def update_store(request,store_id):
    store = Store.objects.get(id=store_id) 
    if request.method == 'POST':
        store.name = request.POST.get('store_name')
        store.address = request.POST.get('store_address')
        store.save()
        return redirect('stores_index')  


class StoreDelete(LoginRequiredMixin,DeleteView):
    model = Store
    success_url = '/stores/'