from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer

from .models import Recipe, Ingredient, Tag

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializers(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipesSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializers(many=True)
    tags = TagSerializer(many=True, required=False)
    image = serializers.ImageField(required=False)
    name = serializers.CharField(max_length=256, required=True)
    text = serializers.CharField(max_length=None, required=True)
    cooking_time = serializers.IntegerField(required=True)

    class Meta:
        model = Recipe
        fields = '__all__'


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password', 'first_name',
                  'last_name')


class AuthTokenSerializer(serializers.Serializer):

