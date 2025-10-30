from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email')
    username = models.CharField(
        max_length=MAX_LENGTH, unique=True,
        validators=[RegexValidator(
            r'^[\w.@+-]+\Z',
            'Имя пользователя должно соответствовать шаблону',
        )],
        verbose_name='Имя пользователя'
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


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
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
