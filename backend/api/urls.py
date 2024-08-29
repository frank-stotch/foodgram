from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views


router_v1 = SimpleRouter()

router_v1.register(
    prefix="users",
    viewset=views.UserViewSet,
    basename="users"
)


urlpatterns = [
    path("", include(router_v1.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
