from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views


app_name = "api"


router_v1 = SimpleRouter()

router_v1.register(
    prefix="users",
    viewset=views.UserViewSet,
    basename="users"
)

router_v1.register(
    prefix="tags",
    viewset=views.TagViewSet,
    basename="tags"
)

router_v1.register(
    prefix="ingredients",
    viewset=views.IngredientViewSet,
    basename="ingredients"
)

router_v1.register(
    prefix="recipes",
    viewset=views.RecipeViewSet,
    basename="recipes"
)


urlpatterns = [
    path("", include(router_v1.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
