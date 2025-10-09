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
    first_name = models.CharField(max_length=MAX_LENGTH,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=MAX_LENGTH,
                                 verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to='users/avatars/',
        null=True,
        verbose_name='Аватар'
    )

    class Meta:
        ordering = ['id']


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
