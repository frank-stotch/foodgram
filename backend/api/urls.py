from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TagViewSet

router_v1 = DefaultRouter()

router_v1.register(prefix="tags", viewset=TagViewSet, basename="tags")

url_patterns = [path("", include(router_v1.urls))]
