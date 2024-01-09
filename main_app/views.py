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


#===== PUBLIC =====

def home(request):
    return render(request, 'home.html')


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
    return redirect('users_detail', user_id=user_id)


@login_required
def users_detail(request, user_id):
    d = datetime.today()
    user = User.objects.get(id=user_id)
    upcoming_rentals = Rental.objects.filter(
        user=user,
        pickup_date__gte=d
    ).order_by('pickup_date')
    past_rentals = Rental.objects.filter(
        user=user,
        dropoff_date__lte=d
    ).order_by('-pickup_date')
    return render(request, 'users/detail.html', {
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
    d = datetime(int(request.POST['dropoff_date'][0:4]),int(request.POST['dropoff_date'][5:7]), int(request.POST['dropoff_date'][8:10]))
    p = datetime(int(request.POST['pickup_date'][0:4]),int(request.POST['pickup_date'][5:7]), int(request.POST['pickup_date'][8:10]))
    days = d - p
    days = days.days
    print(int(request.POST['dropoff_date'][0:4]), 'LOOK HERE!!!')
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
    request.session['selected_car'] = Car.objects.get(id=car_id).id
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
    rental = Rental.objects.get(id=rental_id)
    rental.car = Car.objects.get(id=request.POST['car'])
    rental.pickup_date = request.POST['pickup_date']
    rental.dropoff_date = request.POST['dropoff_date']
    rental.dropoff_location = Store.objects.get(
        id=request.POST['dropoff_location']
    )
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
        return redirect('admin')  
    return render(request, 'admin')
