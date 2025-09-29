from django.http import HttpResponse
from django.db.models import Sum
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
from .models import (Recipe, Tag, Ingredient, Favorite,
                     ShoppingCart, RecipeIngredient)
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

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """
        Добавление/удаление рецепта в список покупок
        """
        recipe = self.get_object()

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite = ShoppingCart.objects.filter(user=request.user,
                                                   recipe=recipe)
            if not favorite.exists():
                return Response(
                    {"detail": "Рецепт не был в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite.delete()
            return Response(
                {"detail": "Рецепт удален из списка покупок."},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """
        Скачать список покупок в виде TXT файла
        GET /api/recipes/download_shopping_cart/
        """
        # Получаем все рецепты в корзине пользователя
        user_cart = ShoppingCart.objects.filter(user=request.user)
        recipes = [cart.recipe for cart in user_cart]

        if not recipes:
            return Response(
                {"detail": "Корзина покупок пуста."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Собираем все ингредиенты с суммарным количеством
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        # Формируем содержимое файла
        shopping_list = []
        shopping_list.append("Foodgram - Список покупок")
        shopping_list.append("=" * 40)
        shopping_list.append("")

        for idx, ingredient in enumerate(ingredients, 1):
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['total_amount']
            shopping_list.append(f"{idx}. {name} - {amount} {unit}")

        shopping_list.append("")
        shopping_list.append("=" * 40)
        shopping_list.append(f"Всего позиций: {len(ingredients)}")
        shopping_list.append(f"Рецептов: {len(recipes)}")
        shopping_list.append("")
        shopping_list.append("Приятных покупок!")

        # Создаем HTTP response с файлом
        file_content = '\n'.join(shopping_list)
        response = HttpResponse(
            file_content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')

        return response


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
