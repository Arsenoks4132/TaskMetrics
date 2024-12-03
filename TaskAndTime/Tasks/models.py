from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model


# Create your models here.
class User(AbstractUser):
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


class Task(models.Model):
    worker = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='tasks'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='tasks'
    )
    spent = models.IntegerField(
        verbose_name='Время'
    )
    time_create = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время завершения'
    )
    comment = models.CharField(
        blank=True,
        verbose_name='Комментарий'
    )
    report = models.FileField(
        upload_to='reports/%Y/%m/%d',
        blank=True,
        null=True,
        default=None,
        verbose_name='Отчёт'
    )
