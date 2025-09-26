from django.db.models import BooleanField, ExpressionWrapper, Q
from django_filters import rest_framework

from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def filter_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__istartswith=value) | Q(name__icontains=value)
        ).annotate(
            startswith=ExpressionWrapper(
                Q(name__istartswith=value),
                output_field=BooleanField()
            )
        ).order_by('-startswith')


class RecipeFilter(rest_framework.FilterSet):

    author = rest_framework.ModelChoiceFilter(
        to_field_name='id',
        queryset=User.objects.all()
    )
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = rest_framework.TypedChoiceFilter(
        choices=[(1, 'true'), (0, 'false')],
        field_name='is_favorited'
    )
    is_in_shopping_cart = rest_framework.TypedChoiceFilter(
        choices=[(1, 'true'), (0, 'false')],
        field_name='is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart'
        )
