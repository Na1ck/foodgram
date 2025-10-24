from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart
from tags.models import Tag
from users.models import Subscription

from .constants import MAX_VALUE, MIN_VALUE

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )


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


class UserSubscriptionSerializer(UserSerializer):
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
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        error_messages={
            'min_value': ('Количество ингредиента не может'
                          f'быть меньше {MIN_VALUE}'),
            'max_value': ('Количество ингредиента не может'
                          f'превышать {MAX_VALUE}'),
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
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(
        required=True,
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        error_messages={
            'min_value': ('Минимальная продолжительность '
                          f'приготовления в минутах - {MIN_VALUE}'),
            'max_value': ('Максимальная продолжительность '
                          f'приготовления в минутах - {MAX_VALUE}'),
            'invalid': 'Продолжительность должна быть целым числом.'
        },
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError("Поле image не может быть null")
        return value

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

        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()

        instance = super().update(instance, validated_data)

        instance.tags.set(tags_data)

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
        return (request
                and request.user.is_authenticated
                and Favorite.objects.filter(user=request.user,
                                            recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request
                and request.user.is_authenticated
                and ShoppingCart.objects.filter(user=request.user,
                                                recipe=obj).exists())


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
