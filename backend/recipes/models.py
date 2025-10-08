from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()

MAX_LENGTH = 256


class RecipeTag(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    tag = models.ForeignKey('tags.Tag', on_delete=models.CASCADE,
                            verbose_name='Тег')

    class Meta:
        unique_together = ('recipe', 'tag')
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey('ingredients.Ingredient',
                                   on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')
    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        unique_together = ('recipe', 'ingredient')
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'


class Recipe(models.Model):
    tags = models.ManyToManyField('tags.Tag', through='RecipeTag',
                                  verbose_name='Теги')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор',
                               related_name='recipes')
    ingredients = models.ManyToManyField('ingredients.Ingredient',
                                         through='RecipeIngredient',
                                         verbose_name='Ингредиенты')
    is_favorited = models.BooleanField(default=False,
                                       verbose_name='В избранном')
    is_in_shopping_cart = models.BooleanField(default=False,
                                              verbose_name='В корзине')
    name = models.CharField(max_length=MAX_LENGTH, verbose_name='Название')
    image = models.ImageField(upload_to='recipes/',
                              verbose_name='Изображение')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления')
    pub_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата публикации',
        db_index=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт')

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт')

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
