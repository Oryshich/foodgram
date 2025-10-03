from itertools import chain

from django.contrib import admin

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    fields = ('ingredient', 'amount')


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
    search_fields = ('author__username', 'name',)
    list_filter = ('tags',)
    readonly_fields = ('count_add_to_favorite_display', 'ingredients_display')
    inlines = (RecipeIngredientInline,)

    @admin.display(description='Tags',)
    def tags_display(self, obj):
        tags = obj.tags.values_list('name')
        return list(chain.from_iterable(tags))

    @admin.display(description='Ingredients',)
    def ingredients_display(self, obj):
        ingredients = obj.ingredients.values_list('name')
        return list(chain.from_iterable(ingredients))

    @admin.display(description='Count in favorites',)
    def count_add_to_favorite_display(self, obj):
        count = obj.favorites.count()
        if count:
            return count


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )
    search_fields = ('name', 'slug')
    list_filter = ('name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
