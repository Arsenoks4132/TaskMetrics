from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator


# Create your models here.
class User(AbstractUser):
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True, verbose_name='Фотография')
    pass


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название',
        unique=True
    )
    cost = models.IntegerField(
        verbose_name='Стоимость'
    )

    def __str__(self):
        return self.name


class Task(models.Model):
    worker = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='tasks'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='tasks',
        null=True,
        blank=False
    )
    spent = models.IntegerField(
        verbose_name='Время',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(24)
        ]
    )
    time_create = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время завершения'
    )
    comment = models.CharField(
        max_length=1000,
        blank=True,
        verbose_name='Комментарий'
    )
    report = models.FileField(
        upload_to='reports/%Y/%m/%d/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Отчёт'
    )
