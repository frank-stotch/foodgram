from django.contrib import admin
from django.urls import include, path

from api.views import RecipeViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("api.urls")),
    path("s/<int:pk>", RecipeViewSet, name="short_link"),
]
