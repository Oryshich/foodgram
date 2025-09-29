from django.contrib import admin
from django.contrib.auth.models import Group

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)

admin.site.unregister(Group)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'name',
        'text',
        'ingredients_display',
        'tags_display',
        'cooking_time',
        'count_add_to_favorite_display',
    )
    search_fields = ('author', 'name',)
    list_filter = ('tags',)
    ordering = ('-id',)
    readonly_fields = ('count_add_to_favorite_display', 'ingredients_display')

    def tags_display(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())
    tags_display.short_description = 'Tags'

    def ingredients_display(self, obj):
        return ', '.join(f'{ingredient.ingredients} ({ingredient.amount})'
                         for ingredient in obj.recipeingredients.all())
    ingredients_display.short_description = 'Ingredients'

    def count_add_to_favorite_display(self, obj):
        return Favorite.objects.filter(recipe=obj).count()
    count_add_to_favorite_display.short_description = 'Count in favorites'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    ordering = ('name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    pass
