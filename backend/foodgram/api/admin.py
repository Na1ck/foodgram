from django.contrib import admin
from .models import Tag, Ingredient, Recipe, RecipeTag, RecipeIngredient

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeTag)
admin.site.register(RecipeIngredient)
