from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.edit import DeleteView
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
  return render(request,'cars/index.html', {
      'cars': cars
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


@login_required
def users_detail(request, user_id):
    user= User.objects.get(id=user_id)
    rentals = Rental.objects.filter(user=user)
    return render(request, 'users/detail.html',{
       'rentals': rentals,
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
def rental_detail(request, rental_id):
    rental = Rental.objects.get(id=rental_id)
    return render(request, 'rentals/detail.html', {
        'rental': rental
    })


class RentalDelete(LoginRequiredMixin, DeleteView):
    model = Rental
    success_url = '/'


@staff_member_required
def admin_page(request):
    return render(request, 'admin.html')
