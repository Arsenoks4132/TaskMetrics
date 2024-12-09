from django.urls import path
from django.contrib.auth.views import LogoutView

from django.views.decorators.cache import cache_page

from . import views

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('login/employee', views.LoginEmployee.as_view(), name='login_employee'),
    path('login/supervisor', views.LoginSupervisor.as_view(), name='login_supervisor'),
    path('registration', views.RegisterUser.as_view(), name='registration'),
    path('profile', cache_page(10)(views.ProfileUser.as_view()), name='profile'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('statistics', cache_page(30)(views.Statistics.as_view()), name='statistics'),
    path('tasks/<int:employee_id>', cache_page(20)(views.TasksList.as_view()), name='tasks_list')
]