from django.urls import path
from .views import welcome,dashboard, end_session, remove_admin, make_admin, add_member, start_session,end_session, members_payble, member_details

urlpatterns = [
    path('', welcome, name='welcome'),
    path('dashboard/', dashboard, name='dashboard'),

    path('make_admin/<int:user_id>/', make_admin, name='make_admin'),
    path('remove_admin/<int:user_id>/', remove_admin, name='remove_admin'),
    path('add_member/', add_member, name='add_member'),

    
    path('members_payble/', members_payble, name='members_payable'),
    path('member_details/<int:user_id>/', member_details, name='member_details'),
    

    path('session/start/', start_session, name='start_session'),
    path('session/end/', end_session, name='end_session'),
    
    
]