from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CreateRecipeSerializer, FavoriteSerializer,
                             IngredientSerializer, ReadRecipeSerializer,
                             ShoppingSerializer, SubscribeSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserSerializer)
from recipes.models import (Ingredient, Recipe, RecipeIngredient, Tag)
from users.models import Subscriptions, User


class CustomUserViewSet(UserViewSet):
    """Вьюсет для пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination
    lookup_field = 'id'

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('PUT', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            if not request.data or (
                request.data.get('avatar') in (None, '', [])
            ):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'avatar': serializer.data.get('avatar')})
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(followers__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None, id=None):
        author_id = id if id is not None else pk
        data = {
            'user': request.user,
            'following': get_object_or_404(User, id=author_id)
        }
        serializer = SubscribeSerializer(
            data={key: obj.id for key, obj in data.items()},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, pk=None, id=None):
        author_id = id if id is not None else pk
        deleted_subscriptions, _ = Subscriptions.objects.filter(
            user=request.user, following=get_object_or_404(User, pk=author_id)
        ).delete()
        if deleted_subscriptions:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"errors": "Необходимо быть подписанным на этого пользователя"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientFilter
    search_fields = ['^name']
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadRecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def helper_shoping_favorite(self, pk, serializer_class):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        object = serializer_class.Meta.model.objects.filter(
            user=user, recipe=recipe
        )
        if self.request.method == 'POST':
            serializer = serializer_class(
                data={'user': user.id, 'recipe': pk},
                context={'request': self.request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if object.exists():
            object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request, pk):
        return self.helper_shoping_favorite(pk, FavoriteSerializer)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        return self.helper_shoping_favorite(pk, ShoppingSerializer)

    def get_export_file(self, list_of_ingredients):
        content = 'Список покупок:\n'

        unique_ingredients = {}
        for ingredient in list_of_ingredients:
            ingredient_name = ingredient['ingredient__name']
            measurement = ingredient['ingredient__measurement_unit']
            amount = ingredient['amount']
            if ingredient_name not in unique_ingredients:
                unique_ingredients[ingredient_name] = (amount, measurement)
            else:
                unique_ingredients[ingredient_name] = (
                    unique_ingredients[ingredient_name][0] + amount,
                    measurement
                )
        for name, amount in unique_ingredients.items():
            content += (f'{name}\t{amount[0]} ({amount[1]})\n')
        return FileResponse(
            content,
            content_type='text/plain',
            filename="shopping_cart.txt",
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')
        return self.get_export_file(ingredients)

    @action(
        detail=True,
        methods=('GET',),
        url_path='get-link',
    )
    def get_link(self, request, pk):
        get_object_or_404(Recipe, pk=pk)
        lnk = request.build_absolute_uri(f'/recipe/{pk}')
        return Response(
            {'short-link': f'{lnk}'},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(AllowAny,),
        url_path='s/<str:short_link>',
    )
    def get_short_link(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect(recipe.get_abs_url())
