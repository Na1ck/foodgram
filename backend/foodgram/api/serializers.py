from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer


from .models import Recipe, Ingredient, RecipeIngredient, Tag

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


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


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
        required=False
    )
    image = serializers.ImageField(required=False)
    name = serializers.CharField(max_length=256, required=True)
    text = serializers.CharField(max_length=None, required=True)
    cooking_time = serializers.IntegerField(required=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["tags"] = TagSerializer(instance.tags.all(),
                                               many=True).data

        recipe_ingredients = RecipeIngredient.objects.filter(recipe=instance)
        representation["ingredients"] = RecipeIngredientReadSerializer(
            recipe_ingredients, many=True
        ).data

        return representation


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password', 'first_name',
                  'last_name')


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        User = get_user_model()

        try:
            user = User.objects.get(email=attrs['email'])

            if not user.check_password(attrs['password']):
                raise serializers.ValidationError("Invalid credentials")

            attrs['user'] = user
            return attrs

        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")
