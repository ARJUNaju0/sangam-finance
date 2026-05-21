from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from accounts.models import User
from django.contrib.auth import get_user_model


User = get_user_model()


def login_view(request):

    if request.method == 'POST':

        identifier = request.POST.get('identifier')
        password = request.POST.get('password')

        user_obj = User.objects.filter(
            username=identifier
        ).first()

        if not user_obj:
            user_obj = User.objects.filter(
                phone=identifier
            ).first()

        if user_obj:

            user = authenticate(
                request,
                username=user_obj.username,
                password=password
            )
            

            if user:
                login(request, user)
                messages.success(request, "Logged in successfully")
                return redirect('dashboard')
        messages.error(request, "Invalid credentials")
                
                
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if User.objects.filter(phone=phone).exists():
            return HttpResponse("User already exists")

        user = User.objects.create(
            name=name,
            phone=phone,
            password=make_password(password),
            role='admin'
        )

        login(request, user)
        return redirect('dashboard')

    return render(request, 'accounts/register.html')
