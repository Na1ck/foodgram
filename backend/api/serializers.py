from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserUserSerializer

from recipes.models import (Recipe, Favorite, ShoppingCart,
                            RecipeIngredient)
from tags.models import Tag
from ingredients.models import Ingredient
from users.models import Subscription

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'first_name', 'last_name', 'is_subscribed', 'avatar')


class UserSubscriptionSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )

    def get_recipes(self, obj):
        """Получаем рецепты автора с учётом лимита"""
        request = self.context.get('request')
        recipes = obj.recipes.all()

        if request:
            limit = request.query_params.get('recipes_limit')
            if limit and limit.isdigit():
                recipes = recipes[:int(limit)]

        return ShortRecipeSerializer(recipes, many=True,
                                     context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=1,
        max_value=1000,
        error_messages={
            'min_value': 'Количество ингредиента не может быть меньше 1.',
            'max_value': 'Количество ингредиента не может превышать 1000.',
            'invalid': 'Количество должно быть числом.'
        },
    )

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'Ингредиент с этим ID не существует.')
        return value


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=1000,
        error_messages={
            'min_value': ('Минимальная продолжительность '
                          'приготовления — 1 минута.'),
            'max_value': ('Максимальная продолжительность '
                          'приготовления — 1000 минут.'),
            'invalid': 'Продолжительность должна быть целым числом.'
        },
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate(self, attrs):
        ingredients_data = attrs.get("ingredients", [])
        tags_data = attrs.get("tags", [])

        if not tags_data:
            raise serializers.ValidationError({
                'tags': ['Добавьте хотя бы один тег.']})

        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError({
                'tags': ['Теги не должны повторяться.']})

        if not ingredients_data:
            raise serializers.ValidationError({
                'ingredients': ['Добавьте хотя бы один ингредиент.']})

        ingredient_ids = [ing['id'] for ing in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': ['Ингредиенты не должны повторяться.']})

        return attrs

    def _process_ingredients(self, instance, ingredients_data):
        """
        Обработчик для удаления текущих и создания новых ингредиентов.
        """
        RecipeIngredient.objects.filter(recipe=instance).delete()
        new_ingredients = [
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ing["id"],
                amount=ing["amount"]
            )
            for ing in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(new_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients", [])
        tags_data = validated_data.pop("tags", [])

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        self._process_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", [])
        tags_data = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data:
            self._process_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    image = serializers.ImageField(read_only=True)
    ingredients = RecipeIngredientReadSerializer(many=True,
                                                 source="recipeingredient_set")
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user,
                                           recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user,
                                               recipe=obj).exists()
        return False


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
            authenticated_user = authenticate(
                username=user.username,
                password=attrs['password']
            )

            if not authenticated_user:
                raise serializers.ValidationError("Invalid credentials")

            self.user = authenticated_user
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid2 credentials")


class AvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']

    def update(self, instance, validated_data):
        if instance.avatar:
            instance.avatar.delete(save=False)

        instance.avatar = validated_data['avatar']
        instance.save()
        return instance
