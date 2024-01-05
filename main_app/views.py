import uuid
import boto3
import os

import datetime

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.edit import DeleteView, UpdateView
from .models import Car, Store, Rental, CreditCard,Photo


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


@login_required
def cars_index(request):
  cars= Car.objects.all()
  photos=Photo.objects.all()
  return render(request,'cars/index.html', {
      'cars': cars,
      'photos':photos

  })


def cars_detail(request, car_id):
    car= Car.objects.get(id=car_id)
    photo= Photo.objects.get(car_id=car_id)
    return render(request, 'cars/detail.html',{
        'car':car,
        'photo':photo
    })




@login_required
def stores_index(request):
    stores = Store.objects.all()
    return render(request,'stores/index.html', {
        'stores': stores,
    })


@login_required
def select_store(request, store_id):
    request.session['selected_store'] = Store.objects.get(id=store_id).name
    return redirect('stores_index')


def users_login(request):
    user_id = request.user.id
    return redirect('users_detail', user_id=user_id)


@login_required
def users_detail(request, user_id):
    d = datetime.date.today()
    user= User.objects.get(id=user_id)
    upcoming_rentals = Rental.objects.filter(user=user, pickup_date__gte=d)
    past_rentals = Rental.objects.filter(user=user, dropoff_date__lte = d)
    return render(request, 'users/detail.html',{
       'upcoming_rentals': upcoming_rentals,
       'past_rentals': past_rentals,
       'user':user

    })


@login_required    
def rentals_new(request):
    stores = Store.objects.all()
    cars = Car.objects.all()
    print(f'{request.GET}')
    return render(request, 'main_app/rental_form.html/', {
        'stores': stores,
        'cars': cars,
    })


@login_required
def rentals_create(request):
    new_rental = Rental.objects.create(
        pickup_date=request.POST['pickup_date'],
        dropoff_date=request.POST['dropoff_date'],
        dropoff_location=Store.objects.get(id=request.POST['dropoff_location']),
        car=Car.objects.get(id=request.POST['car']),
        user=request.user,
        rental_fee=400
    )
    new_rental.save()
    return redirect('users_detail', user_id=request.user.id)


@login_required
def rentals_detail(request, rental_id):
    rental = Rental.objects.get(id=rental_id)
    request.session['selected_store'] = Store.objects.get(id=rental.car.current_store.id).name
    photo = Photo.objects.get(car_id=rental.car)
    return render(request, 'rentals/detail.html', {
        'rental': rental,
        'photo': photo
    })

def rentals_edit(request, rental_id):
    rental =  Rental.objects.get(id=rental_id)
    stores = Store.objects.all()
    cars = Car.objects.all()
    print(rental.pickup_date)
    return render(request, 'rentals/update.html',{
        'rental':rental,
        'stores':stores,
        'cars':cars
    })

def rentals_update(request, rental_id):
    rental = Rental.objects.get(id=rental_id)
    rental.car = Car.objects.get(id=request.POST['car'])
    rental.pickup_date = request.POST['pickup_date']
    rental.dropoff_date = request.POST['dropoff_date']
    rental.dropoff_location = Store.objects.get(id=request.POST['dropoff_location'])
    rental.save()
    return redirect('rentals_detail', rental_id=rental_id)

class RentalDelete(LoginRequiredMixin, DeleteView):
    model = Rental
    success_url = '/'


@staff_member_required
def admin_page(request):
   cars= Car.objects.all()

   return render(request, 'admin.html',{
       'cars':cars
   })


def add_photo(request):

 # photo-file will be the "name" attribute on the <input type="file">
    photo_file = request.FILES.get('photo-file', None)
    car_id= request.POST['car_id']
    if photo_file:
        s3 = boto3.client('s3')
        # need a unique "key" for S3 / needs image file extension too
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # just in case something goes wrong
        try:
            bucket = os.environ['S3_BUCKET']
            s3.upload_fileobj(photo_file, bucket, key)
            # build the full url string
            url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
            # we can assign to cat_id or cat (if you have a cat object)
            Photo.objects.create(url=url, car_id=car_id)
        except Exception as e:
            print('An error occurred uploading file to S3')
            print(e)
    return redirect('admin')



