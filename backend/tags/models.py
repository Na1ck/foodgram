from django.db import models

MAX_LENGTH = 32


class Tag(models.Model):
    name = models.CharField(max_length=MAX_LENGTH, unique=True,
                            verbose_name='Название')
    slug = models.CharField(max_length=MAX_LENGTH, unique=True,
                            null=True, blank=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
