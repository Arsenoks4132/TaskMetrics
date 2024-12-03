from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('login/employee', views.LoginEmployee.as_view(), name='login_employee'),
    path('login/supervisor', views.LoginSupervisor.as_view(), name='login_supervisor'),
    path('registration', views.RegisterUser.as_view(), name='registration')
]
