from rest_framework import filters, viewsets

from recipes.models import Ingredient, Tag
from .serializers import IngredientSerializer, TagSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = ["get"]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = ["get"]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    