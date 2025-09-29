from rest_framework import viewsets
from rest_framework import status
from rest_framework.mixins import (ListModelMixin, CreateModelMixin,
                                   RetrieveModelMixin, UpdateModelMixin,
                                   DestroyModelMixin)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from users.models import User
from .models import Recipe, Tag, Ingredient, Favorite
from .serializers import (RecipesSerializer,
                          ShortRecipeSerializer,
                          TagSerializer,
                          RecipeIngredientReadSerializer,
                          UserSerializer, AuthTokenSerializer)


class RecipesView(ListModelMixin, RetrieveModelMixin,
                  CreateModelMixin, UpdateModelMixin,
                  DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = RecipesSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """
        Добавление/удаление рецепта в избранное
        """
        recipe = self.get_object()

        if request.method == 'POST':
            # Проверяем, не добавлен ли уже рецепт
            if Favorite.objects.filter(user=request.user,
                                       recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            # Проверяем, есть ли рецепт в избранном
            favorite = Favorite.objects.filter(user=request.user,
                                               recipe=recipe)
            if not favorite.exists():
                return Response(
                    {"detail": "Рецепт не был в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite.delete()
            return Response(
                {"detail": "Рецепт удален из избранного."},
                status=status.HTTP_204_NO_CONTENT
            )


class TagsView(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsView(ListModelMixin, RetrieveModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = RecipeIngredientReadSerializer
    queryset = Ingredient.objects.all()


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
