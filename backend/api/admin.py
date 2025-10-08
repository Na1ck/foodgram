from django.contrib import admin

from recipes.models import (Recipe, RecipeTag,
                            RecipeIngredient)
from tags.models import Tag
from ingredients.models import Ingredient

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeTag)
admin.site.register(RecipeIngredient)
