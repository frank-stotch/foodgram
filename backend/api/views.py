from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin

from recipes.models import Ingredient, Recipe, Tag
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    TagSerializer,
    WriteRecipeSerializer,
)


User = get_user_model()


class AvatarViewSet(
    DestroyModelMixin, UpdateModelMixin, viewsets.GenericViewSet
):
    http_method_names = ["put", "delete"]
    queryset = User.objects.all()
    serializer_class = AvatarSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = ["get", "head", "options", "trace"]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = ["get", "head", "options", "trace"]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
        "head",
        "options",
        "trace",
    ]
    queryset = (
        Recipe.objects.prefetch_related("tags", "ingredients")
        .select_related("author")
        .all()
    )

    def get_serializer_class(self):
        if self.request.method in ["POST", "PATCH"]:
            return WriteRecipeSerializer
        return ReadRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)
