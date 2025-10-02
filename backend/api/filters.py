from django_filters import rest_framework

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(rest_framework.FilterSet):

    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = rest_framework.BooleanFilter(
        method='filter_is_favorited'
    )

    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def helper_filter(self, queryset, value, field_filter):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(**{field_filter: user})
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        return self.helper_filter(queryset, value, 'favorites__user')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self.helper_filter(queryset, value, 'shoppingcart__user')
