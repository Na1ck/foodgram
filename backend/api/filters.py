from django_filters.rest_framework import (AllValuesMultipleFilter, CharFilter,
                                           FilterSet, NumberFilter)

from .models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    author = NumberFilter(field_name='author__id')
    tags = AllValuesMultipleFilter(field_name='tags__slug',
                                   method='filter_tags')
    is_favorited = NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = NumberFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        tags_slugs = self.request.GET.getlist('tags')

        if not tags_slugs:
            return queryset

        for tag_slug in tags_slugs:
            queryset = queryset.filter(tags__slug=tag_slug)

        return queryset.distinct()

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует только при is_favorited=1, при 0 - не фильтрует"""
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует только при is_in_shopping_cart=1, при 0 - не фильтрует"""
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset
