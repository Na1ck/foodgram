from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RecipesView, TagsView, UserViewSet, TokenCreateViewSet


router_v1 = DefaultRouter()
router_v1.register('recipes', RecipesView, basename='recipes')
router_v1.register('tags', TagsView, basename='tags')
router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('users/', include('djoser.urls')),
    path('auth/token/login/', TokenCreateViewSet.as_view({'post': 'create'}),
         name='token')
]
