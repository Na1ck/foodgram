from rest_framework import viewsets
from rest_framework.mixins import (ListModelMixin, CreateModelMixin,
                                   RetrieveModelMixin)

from users.models import User
from .models import Recipe, Tag
from .serializers import RecipesSerializer, TagSerializer, UserSerializer


class RecipesView(ListModelMixin, RetrieveModelMixin,
                  CreateModelMixin, viewsets.GenericViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipesSerializer


class TagsView(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
