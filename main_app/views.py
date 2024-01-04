from django import forms
from django.contrib.auth import login
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django.shortcuts import render, redirect
from .models import Car, Store, Rental, CreditCard

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

def home(request):
    return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')

def cars_index(request):
  cars= Car.objects.all()
  return render(request,'cars/index.html',{
      'cars':cars
  })

def stores_index(request):
    stores = Store.objects.all()
    return render(request,'stores/index.html',{
     'stores': stores

    })

def rentals_create(request):
    stores = Store.objects.all()
    cars = Car.objects.all()
    print(f'{request.GET}')
    return render(request, 'main_app/rental_form.html/', {
            'stores': stores,
            'cars': cars
    })


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
