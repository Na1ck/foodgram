from django.http import HttpResponse
from django.db.models import Sum
from rest_framework import viewsets
from rest_framework import status
from rest_framework import filters
from rest_framework.mixins import (ListModelMixin, CreateModelMixin,
                                   RetrieveModelMixin, UpdateModelMixin,
                                   DestroyModelMixin)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (IsAuthenticated)
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, redirect
from rest_framework.decorators import api_view
from djoser.views import UserViewSet as DjoserUserViewSet
from django.contrib.auth import get_user_model

from recipes.models import (Recipe, Favorite,
                            ShoppingCart, RecipeIngredient)
from tags.models import Tag
from ingredients.models import Ingredient
from users.models import Subscription
from .serializers import (RecipesSerializer,
                          ShortRecipeSerializer,
                          TagSerializer,
                          IngredientsSerializer,
                          UserSubscriptionSerializer,
                          AvatarUpdateSerializer)
from .filters import RecipeFilter
from .permissions import IsAuthorOrAdmin, IsAuthenticatedForMe

User = get_user_model()


class RecipesView(ListModelMixin, RetrieveModelMixin,
                  CreateModelMixin, UpdateModelMixin,
                  DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrAdmin]
    serializer_class = RecipesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

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
        """
        user_cart = ShoppingCart.objects.filter(user=request.user)
        recipes = [cart.recipe for cart in user_cart]

        if not recipes:
            return Response(
                {"detail": "Корзина покупок пуста."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

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

        file_content = '\n'.join(shopping_list)
        response = HttpResponse(
            file_content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')

        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """
        Получить короткую ссылку на рецепт
        """
        recipe = self.get_object()

        short_link = request.build_absolute_uri(f'/s/{recipe.id}/')

        return Response({"short-link": short_link})


class TagsView(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsView(ListModelMixin, RetrieveModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = IngredientsSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class UserViewSet(DjoserUserViewSet):
    permission_classes = [IsAuthenticatedForMe]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """
        Получить список подписок пользователя
        """
        subscribed_authors = User.objects.filter(
            following__user=request.user
        )

        page = self.paginate_queryset(subscribed_authors)
        if page is not None:
            serializer = UserSubscriptionSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserSubscriptionSerializer(
            subscribed_authors,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        """
        Подписаться / отписаться
        """
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            if author == user:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user,
                author=author
            )
            if created:
                serializer = UserSubscriptionSerializer(
                    author,
                    context={'request': request}
                )
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(
                user=user,
                author=author
            ).delete()

            if deleted_count:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def update_avatar(self, request):
        """
        Обновить аватар пользователя
        """
        user = request.user
        serializer = AvatarUpdateSerializer(
            user,
            data=request.data,
            partial=False
        )

        if request.method == 'PUT':
            serializer = AvatarUpdateSerializer(
                user,
                data=request.data,
                partial=False
            )

            if serializer.is_valid():
                if user.avatar:
                    user.avatar.delete(save=False)

                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
                return Response(
                    {'message': 'Аватар успешно удален'},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {'error': 'Аватар не установлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )


@api_view(['GET'])
def redirect_short_link(request, recipe_id):
    """Редирект с короткой ссылки на полный рецепт"""
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe_id}/')
