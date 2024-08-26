import csv

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import filters, viewsets
from rest_framework.generics import DestroyAPIView, UpdateAPIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
)

from recipes.models import Ingredient, Recipe, Tag
from .filters import RecipeFilter
from .serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    WriteRecipeSerializer,
)


User = get_user_model()


class AvatarAPIView(DestroyAPIView, UpdateAPIView):
    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["put", "delete", "head", "options", "trace"]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.OK)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.avatar = None
        user.save()
        return Response(status=HTTPStatus.NO_CONTENT)


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
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeFilter
    search_fields = ("name",)

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return WriteRecipeSerializer
        return ReadRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
    )
    def get_link(self, request):
        recipe = self.get_object()
        link = request.build_absolute_uri(recipe.get_absolute_url())
        return Response({"short-link": link})


class ShoppingCartViewSet(
    CreateModelMixin,
    DestroyModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get", "post", "delete", "head", "options", "trace"]
    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.shoppingcarts.select_related("recipe")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, recipe=self.get_recipe())

    def get_recipe(self):
        return get_object_or_404(Recipe, pk=self.kwargs.get("pk"))

    @action(
        detail=False,
        methods=["get"],
        permission_classes=permission_classes,
        url_path="recipes/download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            "attachment; filename=shopping_cart.csv"
        )
        writer = csv.writer(response)
        ingredients = (
            self.get_queryset()
            .values(
                "recipe__ingredients__name",
                "recipe__ingredients__measurement_unit",
            )
            .annotate(amount=Sum("recipe__ingredients__amount"))
        )
        writer.writerow(["Ингредиент", "Единица измерения", "Количество"])
        for ingredient in ingredients:
            writer.writerow(
                [
                    ingredient["recipe__ingredients__name"],
                    ingredient["recipe__ingredients__measurement_unit"],
                    ingredient["amount"],
                ]
            )
        return response


class FavoriteViewSet(
    CreateModelMixin, DestroyModelMixin, viewsets.GenericViewSet
):
    http_method_names = ["post", "delete", "head", "options", "trace"]
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, recipe=self.get_recipe())

    def get_recipe(self):
        return get_object_or_404(Recipe, pk=self.kwargs.get("pk"))

    def get_queryset(self):
        return self.request.user.favorites.select_related("recipe")


class SubscriptionViewSet(
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get", "post", "delete", "head", "options", "trace"]
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.followers.select_related("author")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, author=self.get_author())

    def get_author(self):
        return get_object_or_404(User, pk=self.kwargs.get("pk"))
