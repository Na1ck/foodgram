from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientsView, RecipesView, TagsView, UserViewSet,
                    redirect_short_link)

router_v1 = DefaultRouter()
router_v1.register('recipes', RecipesView, basename='recipes')
router_v1.register('tags', TagsView, basename='tags')
router_v1.register('ingredients', IngredientsView, basename='ingredients')
router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<int:recipe_id>/', redirect_short_link,
         name='short-link-redirect'),
]
