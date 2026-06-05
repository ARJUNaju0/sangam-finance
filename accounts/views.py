from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from accounts.models import User
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


def login_view(request):

    if request.method == "POST":

        login_id = request.POST.get("login_id")
        password = request.POST.get("password")

        try:

            user = User.objects.get(
                Q(username=login_id) |
                Q(phone=login_id)
            )

        except User.DoesNotExist:

            messages.error(
                request,
                "Invalid credentials"
            )

            return redirect("login")

        if user.check_password(password):

            login(request, user)
            messages.success(
                request,
                "Logged in successfully"
            )

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid credentials"
        )

    return render(
        request,
        "accounts/login.html"
    )
def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):

    if User.objects.exists():

        return redirect("login")

    if request.method == "POST":

        User.objects.create_user(
            username=request.POST.get("username"),
            phone=request.POST.get("phone"),
            password=request.POST.get("password"),
            name=request.POST.get("name"),
            role="admin",
            is_staff=True
        )

        messages.success(
            request,
            "Admin account created successfully"
        )

        return redirect("login")

    return render(
        request,
        "accounts/register.html"
    )