from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response


from api.serializers import (
    AvatarSerializer,
    CreateRecipeSerializer,
    IngredientSerializer,
    ReadFollowSerializer,
    WriteFollowSerializer,
    ReadRecipeSerializer,
    ShortRecipeSerializer,
    TagSerializer,
    UserSerializer,
)
from .pagination import MyPagination
from .filters import IngredientFilter, RecipeFilter
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    Shopping_list,
    Tag
)
from users.models import Follow, User
from .permissions import IsAuthorOrReadOnly, ReadOnly


class UserViewSet(DjoserUserViewSet):

    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, ReadOnly)
    pagination_class = MyPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated, )
        return super().get_permissions()
    
    @action(
        detail=False,
        methods=('PUT',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        if 'avatar' not in request.data:
            return Response(
                {'avatar': 'Отсутствует изображение'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        avatar_data = serializer.validated_data.get('avatar')

        request.user.avatar = avatar_data
        request.user.save()

        image_url = request.build_absolute_uri(
            f'/media/users/images/{avatar_data.name}'
        )
        return Response(
            {'avatar': str(image_url)}, status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def del_avatar(self, request):
        if self.request.user.avatar is not None:
            self.request.user.avatar.delete(save=False)
            self.request.user.avatar = None
            self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET', 'PUT', 'PATCH', 'DELETE'),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=('GET',),
        url_path='subscriptions',
    )
    def get_my_follows(self, request):
        user = request.user
        user_following = User.objects.filter(following__user=user)
        serializer = ReadFollowSerializer(
            self.paginate_queryset(user_following),
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        user = get_object_or_404(User, pk=id)
        if request.user == user:
            raise ValidationError('Нельзя подписываться на самого себя')
        _, created = Follow.objects.get_or_create(
            following=user,
            user=request.user
        )
        if not created:
            raise ValidationError('Уже подписан')
        return Response(
            WriteFollowSerializer(user, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
    
    @subscribe.mapping.delete
    def del_subscribe(self, request, id):
        user = get_object_or_404(User, pk=id)
        get_object_or_404(
            Follow,
            following=user,
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (
        Recipe.objects.prefetch_related('tags', 'ingredients')
        .select_related('author')
        .all()
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = MyPagination
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadRecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)

    def partial_update(self, request):
        instance = self.get_object()
        data = request.data.copy()

        serializer = self.get_serializer(
            instance,
            data=data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        super().perform_update(serializer)
        return Response(serializer.data)
    
    def get_permissions(self):
        if (
            self.action == 'download_shopping_cart' 
            or self.request.method == 'POST'
        ):
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(
        detail=True,
        methods=('GET',),
        permission_classes=(IsAuthorOrReadOnly,),
        url_path='get-link',
    )
    def get_link(self, request, **kwargs):
        lnk = (
            f'{request.schema}://{request.get_host()}'
            f'/s/{self.get_object().short_url}'
        )
        return Response({'short-link': lnk}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_list(self, request):
        ingredients = RecipeIngredients.objects.filter(
            recipe__shopping_lists__user=request.user
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
            filename="shopping_cart.txt"
        )

    @staticmethod
    def helper_for_favorite_shopping(request, dest_list_name, pk, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'DELETE':
            get_object_or_404(model, recipe=recipe, user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        _, created = model.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            raise ValidationError(f'Уже есть в списке {dest_list_name}')
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        url_path=r'(?P<id>\d+)/favorite',
    )
    def favorite(self, request, pk):
        return self.helper_for_favorite_shopping(
            request,
            dest_list_name='избранного',
            pk=pk,
            model=Favorite,
        )

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        url_path=r'(?P<id>\d+)/shopping_cart',
    )
    def shopping_cart(self, request, pk):
        return self.helper_for_favorite_shopping(
            request,
            dest_list_name='покупок',
            pk=pk,
            model=Shopping_list,
        )
