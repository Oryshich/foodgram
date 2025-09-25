from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

app_name = 'api'
v1_route = SimpleRouter()

v1_route.register('users', UserViewSet, basename='users')
v1_route.register('tags', TagViewSet, basename='tags')
v1_route.register('ingredients', IngredientViewSet, basename='ingredients')
v1_route.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(v1_route.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
