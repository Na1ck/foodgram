from django.db import models

from .constants import MAX_LENGTH


class Tag(models.Model):
    name = models.CharField(max_length=MAX_LENGTH, unique=True,
                            verbose_name='Название')
    slug = models.CharField(max_length=MAX_LENGTH, unique=True,
                            null=True, blank=True, verbose_name='Слаг')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
