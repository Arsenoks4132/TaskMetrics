from django.views.generic import TemplateView, CreateView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import LoginUserForm, RegisterUserForm


# Create your views here.
class HomePage(TemplateView):
    template_name = 'Tasks/index.html'
    extra_context = {'title': 'Домашняя страница'}


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'Tasks/login.html'

    def get_success_url(self):
        return reverse_lazy('home')


class LoginEmployee(LoginUser):
    extra_context = {
        'title': 'Авторизация',
        'login_type': 'Сотрудника',
        'button_text': 'Войти'
    }


class LoginSupervisor(LoginUser):
    extra_context = {
        'title': 'Авторизация',
        'login_type': 'Руководителя',
        'button_text': 'Войти'
    }
    success_url = reverse_lazy('home')


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'Tasks/login.html'
    extra_context = {
        'title': 'Регистрация',
        'button_text': 'Зарегистрироваться'
    }

    def get_success_url(self):
        return reverse_lazy('login_employee')
