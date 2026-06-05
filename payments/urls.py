from django.urls import path
from .views import payment_ledger, save_and_close_session

urlpatterns = [
    path('',payment_ledger,name='payment_ledger'),
    path('payments/save-and-close/', save_and_close_session, name='save_and_close_session'),
    
    
] 