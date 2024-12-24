from django.urls import path
from .views import *

app_name = 'api'

urlpatterns = [
    path('login/', do_login, name='login'),
    path('s/', get_salt, name='get_salt'),
    path('update/', update_user_info, name='update'),
    path('updatePassword/', update_password, name='update_password'),
    path('register/', do_register, name='register'),
    path('check-auth/', check_login, name='check_login'),
    path('logout/', do_logout, name='logout'),
    path('mypage/', get_user_data, name='mydata'),
    path('history/', get_access_history, name='mydata'),
    path('getAddressInfo/', get_address_info, name='get_address_info'),
]