from django.core.validators import MinValueValidator
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from recipes.models import (Ingredient, Recipe, RecipeIngredient, ShoppingCart,
                            Tag)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from api.constants import MIN_AMOUNT, MIN_COOKING_TIME
from api.fields import Base64ImageField
from users.models import User


class UserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        return (
            user.is_authenticated
            and obj.followers.filter(user=user).exists()
        )


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            'avatar'
        )


class BaseUserSerializer(serializers.ModelSerializer):
    """Базовый cериализатор пользователя. (Необходим для Postman)."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class AddIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов при добавлении в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для списка продуктов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer):
    """Сериализатор подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if request is not None:
            recipes_limit = request.GET.get('recipes_limit')
            if recipes_limit:
                try:
                    recipes_count = int(recipes_limit)
                    if recipes_count >= 0:
                        recipes = recipes[:recipes_count]
                except (TypeError, ValueError):
                    pass

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериалайзер для корзины покупок."""

    author = DjoserUserSerializer
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = ShoppingCart
        fields = ('author', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('author', 'recipe'),
                message='Повторное внесение в корзину покупок запрещено'
            ),
        ]


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
    )
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.favorites.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецепте."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_id(self, id):
        if not id:
            raise ValidationError('Отсутствуют id ингредиента в рецепте !!!')
        if not Ingredient.objects.filter(id=id).exists():
            raise ValidationError('Такой ингредиент не найден !!!')
        return id

    def validate_amount(self, amount):
        if not amount:
            raise ValidationError('Отсутствует кол-во ингредиента !!!')
        if amount < MIN_AMOUNT:
            raise ValidationError(f'Количество < {MIN_AMOUNT} !!!')
        return amount


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientCreateSerializer(
        many=True,
        write_only=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def helper_validate_tags(self, tags):
        if tags is None:
            raise ValidationError('Отсутствуют теги !!!')
        if not isinstance(tags, list) or len(tags) == 0:
            raise ValidationError('Должен быть как минимум 1 тег.')
        tag_ids = [item.id for item in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise ValidationError('Теги должны быть уникальны.')

    def helper_validate_ingredients(self, ingredients):
        if ingredients is None:
            raise ValidationError('Отсутствуют ингредиенты !!!')
        if not isinstance(ingredients, list) or len(ingredients) == 0:
            raise ValidationError('Должен быть как минимум 1 ингредиент.')
        ingredients_id = [item.get('id') for item in ingredients]
        if len(ingredients_id) != len(set(ingredients_id)):
            raise ValidationError('Ингредиенты повторяются!!!')

    def helper_validate_cooking_time(self, cooking_time):
        if cooking_time is None:
            raise ValidationError('Не указано время приготовления !!!')
        if int(cooking_time) < MIN_COOKING_TIME:
            raise ValidationError(
                f'Время приготовления < {MIN_COOKING_TIME} !!!'
            )

    def validate(self, data):
        self.helper_validate_tags(data.get('tags'))
        self.helper_validate_ingredients(data.get('ingredients'))
        self.helper_validate_cooking_time(data.get('cooking_time'))
        return data

    def helper_add_ingredients(self, recipe, ingredients):
        for ingredient_data in ingredients:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.helper_add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        instance.tags.set(tags)
        self.helper_validate_ingredients(ingredients)
        instance.recipeingredient_set.all().delete()
        self.helper_add_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data
