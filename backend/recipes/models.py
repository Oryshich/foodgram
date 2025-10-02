from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from recipes.constants import (MAX_LENGTH_FIELD,
                               MAX_LENGTH_INGREDIENT_MEASUREMENT_UNIT,
                               MAX_LENGTH_INGREDIENT_NAME, MAX_LENGTH_TAG_NAME,
                               MAX_LENGTH_TAG_SLUG, MIN_AMOUNT,
                               MIN_COOKING_TIME)
from recipes.utils import generate_short_link
from users.models import User


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True,
        verbose_name='Slug',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        unique=True
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_MEASUREMENT_UNIT,
        verbose_name='Единица измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_pair_name_measurement_unit',
            ),
        )

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_FIELD
    )
    image = models.ImageField(
        'Фото блюда',
        blank=True,
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Текстовое описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        verbose_name='Тег',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f'Не может быть меньше {MIN_COOKING_TIME} минут(ы)'
            ),
        ],
        verbose_name='Время приготовления в минутах'
    )

    add_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления рецепта',
    )
    short_link = models.CharField(
        verbose_name='Короткая ссылка на рецепт',
        default=generate_short_link,
        max_length=MAX_LENGTH_FIELD
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'name'),
                name='unique_pair_author_name',
            ),
        )

    def __str__(self):
        return f'Рецепт {self.name} от {self.author}'

    def get_abs_url(self):
        return reverse('recipes:short_link', args=[self.pk])


class RecipeIngredient(models.Model):
    """Модель для связи рецепта и списка продуктов (ингредиентов)."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message=f'Не может быть меньше {MIN_AMOUNT}'
            ),
        ],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('recipe', 'ingredient')
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_pair_recipe_ingredient',
            ),
        )

    def __str__(self):
        return f'Для рецепта {self.recipe} ингредиент {self.ingredient}'


class RecipeTag(models.Model):
    """Модель для связи рецепта и тегов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='unique_pair_recipe_tag',
            ),
        )


class BaseUserRecipe(models.Model):
    """Абстрактная модель для избранного и списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_abstract_pair_user_recipe',
            ),
        )

    def __str__(self):
        return f'Рецепт {self.recipe} от {self.user}'


class Favorite(BaseUserRecipe):
    """Модель для избранных рецептов."""

    class Meta:
        ordering = ('user',)
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(BaseUserRecipe):
    """Модель для списка покупок."""

    class Meta:
        ordering = ('user',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
