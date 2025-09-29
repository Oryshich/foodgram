from django.db import IntegrityError
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


from api.serializers import (
    BaseUserSerializer,
    CreateRecipeSerializer,
    CustomCreateUserSerializer,
    CustomUserSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    RecipeShortSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from .pagination import LimitPageNumberPagination
from .filters import IngredientFilter, RecipeFilter
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from users.models import Subscriptions, User
from .permissions import IsAuthorOrReadOnly, ReadOnly


class CustomUserViewSet(UserViewSet):
    """Вьюсет для пользователей."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitPageNumberPagination
    lookup_field = 'id'

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = CustomCreateUserSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = User.objects.get(email=serializer.validated_data['email'])
        minimal = BaseUserSerializer(user, context={'request': request})
        headers = self.get_success_headers(minimal.data)
        return Response(
            minimal.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

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
        elif request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(current_password):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
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
        if pages is not None:
            serializer = SubscriptionSerializer(
                pages,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None, id=None):
        try:
            user = request.user
            author_id = id if id is not None else pk
            author = User.objects.filter(id=author_id).first()
            if author is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if user == author:
                # Подписка на самого себя запрещена
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                (subscription,
                    created) = Subscriptions.objects.get_or_create(
                    user=user, following=author
                )
            except IntegrityError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if not created:
                # Подписка не создана !
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @subscribe.mapping.delete
    def del_subscribe(self, request, pk=None, id=None):
        try:
            user = request.user
            author_id = id if id is not None else pk
            author = User.objects.filter(id=author_id).first()
            if author is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            subscription = Subscriptions.objects.filter(
                user=user,
                following=author
            )
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


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
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return CreateRecipeSerializer
        return ReadRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def helper_favorite_shopping(self, request, recipe, model):
        user = request.user
        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if not created:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeShortSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        dataset = model.objects.filter(user=user, recipe=recipe)
        if dataset.exists():
            dataset.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request, pk):
        recipe = self.get_object()
        return self.helper_favorite_shopping(request, recipe, Favorite)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        recipe = self.get_object()
        return self.helper_favorite_shopping(request, recipe, ShoppingCart)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')
        unique_ingredients = {}
        for ingredient in ingredients:
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
        content = 'Список покупок:\n'
        for ingredient_name, amount_measurement in unique_ingredients.items():
            content += (
                f'{ingredient_name}\t{amount_measurement[0]} '
                f'({amount_measurement[1]})\n'
            )
        return FileResponse(
            content,
            content_type='text/plain',
            filename="shopping_cart.txt",
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=('GET',),
        url_path='get-link',
    )
    def get_link(self, request, pk):
        try:
            recipe = self.get_object()
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        scheme = request.scheme
        host = request.get_host()
        lnk = f'{scheme}://{host}'
        return Response(
            {'short-link': f'{lnk}/s/{recipe.short_link}'},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(ReadOnly,),
        url_path='s/<str:short_link>',
    )
    def get_short_link(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect(recipe.get_abs_url())
