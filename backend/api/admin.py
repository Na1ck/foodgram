from django.contrib import admin
from ingredients.models import Ingredient
from recipes.models import Recipe, RecipeIngredient, RecipeTag
from tags.models import Tag

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeTag)
admin.site.register(RecipeIngredient)
