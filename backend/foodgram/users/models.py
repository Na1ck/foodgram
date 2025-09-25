# models.py
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

ROLE_CHOICES = [
    ('user', 'User'),
    ('moderator', 'Moderator'),
    ('admin', 'Admin'),
]

MAX_LENGTH = 150


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email')
    username = models.CharField(
        max_length=MAX_LENGTH, unique=True,
        validators=[RegexValidator(
            r'^[\w.@+-]+\Z',
            'Имя пользователя должно соответствовать шаблону',
        )]
    )
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    is_subscribed = models.BooleanField(default=False, verbose_name='Подписка')

    class Meta:
        ordering = ['id']
