from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AvatarAPIView,
    FavoriteViewSet,
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
    TagViewSet,
)

router_v1 = DefaultRouter()

router_v1.register(prefix="tags", viewset=TagViewSet, basename="tags")
router_v1.register(
    prefix="ingredients", viewset=IngredientViewSet, basename="ingredients"
)
router_v1.register(prefix="recipes", viewset=RecipeViewSet, basename="recipes")

router_v1.register(
    prefix="recipes/<int:pk>/shopping_cart",
    viewset=ShoppingCartViewSet,
    basename="shopping_cart",
)

router_v1.register(
    prefix="recipes/<int:pk>/favorite",
    viewset=FavoriteViewSet,
    basename="favorite",
)

urlpatterns = [
    path("", include(router_v1.urls)),
    path("users/me/avatar/", AvatarAPIView.as_view(), name="avatar"),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
