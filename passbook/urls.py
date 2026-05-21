from django.urls import path
from .views import passbook

urlpatterns = [
    path('passbook/', passbook, name='passbook'),
]