import base64

from django.contrib.auth import authenticate, get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')


class UserCreateSerializer(UserCreateSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'password')


class UserSubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_subscribed', 'avatar', 'recipes_count', 'recipes'
        ]

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')

        recipes = obj.recipes.all()

        if request:
            recipes_limit_param = request.query_params.get('recipes_limit')
            if recipes_limit_param and recipes_limit_param.isdigit():
                recipes_limit = int(recipes_limit_param)
                recipes = recipes[:recipes_limit]

        return ShortRecipeSerializer(recipes, many=True,
                                     context=self.context).data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(required=True)

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipesSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    name = serializers.CharField(max_length=256, required=True)
    text = serializers.CharField(max_length=None, required=True)
    cooking_time = serializers.IntegerField(required=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def validate(self, attrs):
        ingredients_data = self.initial_data.get("ingredients", [])
        tags_data = self.initial_data.get("tags", [])
        cooking_time_data = self.initial_data.get("cooking_time")

        if cooking_time_data < 1:
            raise serializers.ValidationError({
                "cooking_time": "Должно быть больше 1"
            })

        if not tags_data:
            raise serializers.ValidationError({
                "tag": ["Добавьте хотя бы один тег."]
            })

        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError({
                "tags": ["Теги не должны повторяться."]
            })

        if not ingredients_data:
            raise serializers.ValidationError({
                "ingredients": ["Добавьте хотя бы один ингредиент."]
            })

        ingredient_ids = [ing['id'] for ing in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                "ingredients": ["Ингредиенты не должны повторяться."]
            })

        for ing in ingredients_data:
            if ing['amount'] < 1:
                raise serializers.ValidationError({
                    "ingredients": ["Ингредиентов должно быть больше 0"]
                })
            if not Ingredient.objects.filter(id=ing['id']).exists():
                raise serializers.ValidationError({
                    "ingredients": ["Ингредиент не существует."]
                })

        return attrs

    def get_is_favorited(self, obj):
        """
        Возвращает True, если текущий пользователь добавил рецепт в избранное
        """
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

    def create(self, validated_data):
        ingredients_data = self.initial_data.get("ingredients", [])
        tags_data = validated_data.pop("tags", [])

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        for ing in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ing["id"],
                amount=ing["amount"]
            )

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = self.initial_data.get("ingredients", [])
        tags_data = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data:
            RecipeIngredient.objects.filter(recipe=instance).delete()

            for ing in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ing["id"],
                    amount=ing["amount"]
                )

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["tags"] = TagSerializer(instance.tags.all(),
                                               many=True).data

        recipe_ingredients = RecipeIngredient.objects.filter(recipe=instance)
        representation["ingredients"] = RecipeIngredientReadSerializer(
            recipe_ingredients, many=True
        ).data

        return representation


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
