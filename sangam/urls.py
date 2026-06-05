from django.urls import path
from .views import group_settings,welcome,dashboard,member_detail, end_session, add_member, start_session,end_session, make_admin, remove_admin, save_and_close_session

urlpatterns = [
    path('', welcome, name='welcome'),
    path('dashboard/', dashboard, name='dashboard'),

    path('make_admin/<int:user_id>/', make_admin, name='make_admin'),
    path('remove_admin/<int:user_id>/', remove_admin, name='remove_admin'),

    path('add_member/', add_member, name='add_member'),

    path('session/start/', start_session, name='start_session'),
    path('session/end/', end_session, name='end_session'),

    path('group-settings/',group_settings,name='group_settings'),
    path("session/save-close/",save_and_close_session,name="save_and_close_session"),
    path('member/<int:user_id>/', member_detail, name='member_detail'),

    
]