from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from .constants import MAX_LENGTH_FIELD

User = get_user_model()


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_FIELD,
        unique=True,
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_FIELD,
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
        max_length=MAX_LENGTH_FIELD,
        unique=True
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_FIELD,
        verbose_name='Единица измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации (пользователь)',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_FIELD
    )
    image = models.ImageField(
        'Картинка',
        blank=True,
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Текстовое описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTags',
        verbose_name='Тег',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, message='Не может быть меньше 1 минуты'),
        ],
        verbose_name='Время приготовления в минутах'
    )

    add_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления рецепта',
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


class RecipeIngredients(models.Model):
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
            MinValueValidator(1, message='Не может быть меньше 1'),
        ],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'recipe_ingredients'
        ordering = ('recipe', 'ingredient')
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_pair_recipe_ingredients',
            ),
        )

    def __str__(self):
        return f'Для рецепта {self.recipe} ингредиент {self.ingredient}'


class RecipeTags(models.Model):
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
        default_related_name = 'recipe_tags'
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'


class BaseUserRecipe(models.Model):
    """Абстрактная модель для избранного и списка покупок."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'recipe'),
                name='unique_pair_author_recipe',
            ),
        )

    def __str__(self):
        return f'Рецепт {self.recipe} от {self.user}'


class Favorite(BaseUserRecipe):
    """Модель для избранного."""

    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class Shopping_list(BaseUserRecipe):
    """Модель для списка покупок."""

    class Meta:
        default_related_name = 'shopping_lists'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
