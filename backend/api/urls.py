from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AvatarViewSet, IngredientViewSet, RecipeViewSet, TagViewSet

router_v1 = DefaultRouter()

router_v1.register(prefix="tags", viewset=TagViewSet, basename="tags")
router_v1.register(
    prefix="ingredients", viewset=IngredientViewSet, basename="ingredients"
)
router_v1.register(prefix="recipes", viewset=RecipeViewSet, basename="recipes")

router_v1.register(
    prefix="users/me/avatar", viewset=AvatarViewSet, basename="avatar"
)

url_patterns = [path("", include(router_v1.urls))]
