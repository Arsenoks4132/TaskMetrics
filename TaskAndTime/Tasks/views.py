from django.db.models import Sum, F, Count
from django.views.generic import TemplateView, CreateView, DetailView, ListView
from django.contrib.auth.views import LoginView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

from .forms import LoginUserForm, RegisterUserForm, AddTaskForm
from .models import Task
from TaskAndTime import settings


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

    def get_success_url(self):
        return reverse_lazy('profile')


class LoginSupervisor(LoginUser):
    extra_context = {
        'title': 'Авторизация',
        'login_type': 'Руководителя',
        'button_text': 'Войти'
    }

    def get_success_url(self):
        return reverse_lazy('statistics')


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'Tasks/login.html'
    extra_context = {
        'title': 'Регистрация',
        'button_text': 'Зарегистрироваться'
    }

    def get_success_url(self):
        return reverse_lazy('login_employee')


class ProfileUser(LoginRequiredMixin, CreateView, DetailView):
    model = get_user_model()
    form_class = AddTaskForm
    template_name = 'Tasks/profile.html'

    extra_context = {
        'title': 'Профиль',
        'default_image': settings.DEFAULT_PROFILE_IMAGE,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = Task.objects.filter(worker=self.request.user)
        hours = 0
        if tasks:
            hours = tasks.aggregate(total=Sum('spent'))['total']
        context = {
            **context,
            'tasks_count': tasks.count(),
            'hours_count': hours
        }
        return context

    def get_success_url(self):
        return reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        t = form.save(commit=False)
        t.worker = self.request.user
        return super().form_valid(form)


class Statistics(ListView):
    template_name = 'Tasks/statistics.html'
    context_object_name = 'employees'

    extra_context = {
        'title': 'Статистика',
    }

    def get_queryset(self):
        tasks = Task.objects.annotate(total=F('spent') * F('category__cost')).values('worker').annotate(
            sum=Sum('total'), count=Count('worker'), hours=Sum('spent'), name=F('worker__first_name'),
            surname=F('worker__last_name'), email=F('worker__email'))
        return tasks
