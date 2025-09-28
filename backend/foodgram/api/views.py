from rest_framework import viewsets
from rest_framework.mixins import (ListModelMixin, CreateModelMixin,
                                   RetrieveModelMixin)
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from .models import Recipe, Tag
from .serializers import (RecipesSerializer, TagSerializer,
                          UserSerializer, AuthTokenSerializer)


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


class TokenCreateViewSet(ViewSet):
    def create(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'auth_token': str(refresh.access_token),
        })
