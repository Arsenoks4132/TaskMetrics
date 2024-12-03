# Generated by Django 5.1.3 on 2024-12-03 15:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Tasks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Название')),
                ('cost', models.IntegerField(verbose_name='Стоимость')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spent', models.IntegerField(verbose_name='Время')),
                ('time_create', models.DateTimeField(auto_now_add=True, verbose_name='Время завершения')),
                ('comment', models.CharField(blank=True, verbose_name='Комментарий')),
                ('report', models.FileField(blank=True, default=None, null=True, upload_to='reports/%Y/%m/%d', verbose_name='Отчёт')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='Tasks.category')),
                ('worker', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tasks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]