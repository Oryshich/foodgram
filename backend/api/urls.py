from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)

app_name = 'api'
route = SimpleRouter()

route.register('users', CustomUserViewSet, basename='users')
route.register('tags', TagViewSet, basename='tags')
route.register('ingredients', IngredientViewSet, basename='ingredients')
route.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(route.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
