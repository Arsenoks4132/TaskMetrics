from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('login/employee', views.LoginEmployee.as_view(), name='login_employee'),
    path('login/supervisor', views.LoginSupervisor.as_view(), name='login_supervisor'),
    path('registration', views.RegisterUser.as_view(), name='registration'),
    path('profile', views.ProfileUser.as_view(), name='profile'),
    path('logout', LogoutView.as_view(), name='logout')
]
