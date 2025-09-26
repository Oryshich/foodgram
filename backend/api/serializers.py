import base64
from email.policy import default

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    Shopping_list,
    Tag
)
from users.models import User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CurrentUserSerializer(DjoserUserSerializer):
    """Сериализатор для текущего пользователя."""

    is_subscribed = serializers.BooleanField(
        default=False,
        read_only=True
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )


class UserSerializer(CurrentUserSerializer):
    """Сериализатор для пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.following.filter(user=user).exists()
        )


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
        fields = '__all__'


class AddIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов при добавлении в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для списка продуктов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name') 
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientsSerializer(
        many=True,
        required=False,
        source='recipe_ingredients'
    )
    image = Base64ImageField(required=True)
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
            'cooking_time',
        )
        read_only_fields = fields
    
    def helper_exist(self, obj, model):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and model.objects.filter(author=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return self.helper_exist(obj, Shopping_list)

    def get_is_favorited(self, obj):
        return self.helper_exist(obj, Favorite)


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    ingredients = AddIngredientSerializer(
        many=True,
        write_only=True,
    )
    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(1, message='Не может быть меньше 1'),
        ],
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'author',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise ValidationError('Отсутствуют ингредиенты !!!')
        ingredients_id = [id['id'] for id in ingredients]
        if len(ingredients_id) != len(set(ingredients_id)):
            raise ValidationError('Ингредиенты повторяются!!!')
        tags = data.get('tags')
        if not tags:
            raise ValidationError('Отсутствуют теги !!!')
        return data

    def add_ingredients(self, ingredients, recipe):
        """Сохранение в БД ингридиентов рецепта."""
        for ingredient in ingredients:
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount'))

    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Внесение изменений в рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')

        recipe = super().update(instance, validated_data)
        instance.recipe_ingredients.all().delete()
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)
        return instance

    def to_representation(self, recipe):
        return ReadRecipeSerializer(recipe, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для показа рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ReadFollowSerializer(UserSerializer):
    """Сериализатор для чтения подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.author)
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.following.filter(user=user).exists()
        )


class WriteFollowSerializer(UserSerializer):
    """Сериализатор для записи подписок."""

    author_recipe = UserSerializer
    user = UserSerializer

    class Meta:
        model = Favorite
        fields = ('author_recipe', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('author_recipe', 'user'),
                message='Повторная подписка запрещена'
            ),
        ]
    
    def validate_user(self, value):
        if self.context.get('request').author_recipe == value:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return value

    def to_representation(self, instance):
        return ReadFollowSerializer(
            instance.author_recipe,
            context={'request': self.context.get('request')}
        ).data


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для изображения профиля."""

    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('avatar',)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для избранных рецептов."""

    author = UserSerializer
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('author', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('author', 'user'),
                message='Повторное внесение в избранное запрещено'
            ),
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериалайзер для корзины покупок."""

    author = UserSerializer
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = Shopping_list
        fields = ('author', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Shopping_list.objects.all(),
                fields=('author', 'user'),
                message='Повторное внесение в корзину покупок запрещено'
            ),
        ]
