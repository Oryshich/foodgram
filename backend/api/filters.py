from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )

    is_in_shopping_cart = filters.BooleanFilter(
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
        if value:
            if user.is_authenticated:
                return queryset.filter(**{field_filter: user})
            else:
                return queryset.none()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        return self.helper_filter(queryset, value, 'favorites__user')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self.helper_filter(queryset, value, 'shoppingcart__user')
