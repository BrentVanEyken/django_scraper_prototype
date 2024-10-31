from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegisterForm
from datetime import datetime

@login_required
def home(request):
    current_year = datetime.now().year
    return render(request, 'home.html', {'current_year': current_year})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('home')
        else:
            messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = RegisterForm()
    current_year = datetime.now().year
    return render(request, 'registration/register.html', {'form': form, 'current_year': current_year})