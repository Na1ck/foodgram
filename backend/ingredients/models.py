from django.db import models

from .constants import NAME_MAX_LENGTH, UNIT_MAX_LENGTH


class Ingredient(models.Model):
    name = models.CharField(max_length=NAME_MAX_LENGTH,
                            verbose_name='Название')
    measurement_unit = models.CharField(max_length=UNIT_MAX_LENGTH,
                                        verbose_name='Единица измерения')

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
