from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Task, Category


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form__input'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form__input'})
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'password']


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form__input'})
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form__input'})
    )
    password2 = forms.CharField(
        label='Повтор пароля',
        widget=forms.PasswordInput(attrs={'class': 'form__input'})
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name', 'photo', 'password1', 'password2']
        labels = {
            'email': 'E-mail',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'photo': 'Фотография',
        }
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form__input'}),
            'first_name': forms.TextInput(attrs={'class': 'form__input'}),
            'last_name': forms.TextInput(attrs={'class': 'form__input'}),
            'photo': forms.FileInput(attrs={'class': 'form__file'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.Meta.model.objects.filter(email=email).exists():
            raise ValidationError('Уже существует пользователь с таким E-mail')
        return email


class AddTaskForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label='Тип задачи не выбран',
        label='Тип задачи',
        widget=forms.Select(attrs={'class': 'form__select'})
    )

    class Meta:
        model = Task
        fields = ['category', 'spent', 'comment', 'report']
        widgets = {
            'spent': forms.NumberInput(attrs={'class': 'form__input', 'min': 1}),
            'comment': forms.Textarea(attrs={'class': 'form__input'}),
            'report': forms.FileInput(attrs={'class': 'form__file'}),
        }
        labels = {
            'spent': 'Затраченное время',
            'comment': 'Комментарий (опционально)',
            'report': 'Отчёт (опционально)'
        }
