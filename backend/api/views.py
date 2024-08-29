import csv

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from .constants import InvalidErrorMessage
from .filters import IngredientFilter, RecipeFilterSet
from .pagination import (
    LimitPageNumberPagination,
)
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    ShoppingCartSerializer,
    ReadSubscriptionSerializer,
    WriteSubscriptionSerializer,
    TagSerializer,
    WriteRecipeSerializer,
)


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    def get_permissions(self):
        if self.action == "me":
            return [IsAuthenticated()]
        if self.action == "retrieve":
            return [AllowAny()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = AvatarSerializer(data=request.data)
            if serializer.is_valid():
                user.avatar = serializer.validated_data["avatar"]
                user.save()
                return Response(
                    AvatarSerializer(user).data, status=HTTPStatus.OK
                )
            return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)
        user.avatar.delete(save=True)
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=False,
        methods=["GET"],
        pagination_class=LimitPageNumberPagination,
    )
    def subscriptions(self, request):
        queryset = request.user.subscribers.all()
        serializer = ReadSubscriptionSerializer(
            self.paginate_queryset(queryset),
            many=True,
            context={"request": request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == "POST":
            serializer = WriteSubscriptionSerializer(
                data={"subscriber": user.pk, "author": author.pk},
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)
        subscription = user.subscribers.filter(author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            {"errors": InvalidErrorMessage.ALREADY_SUBSCRIBED},
            status=HTTPStatus.BAD_REQUEST,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = ["get", "head", "options", "trace"]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = ["get", "head", "options", "trace"]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientFilter,)
    search_fields = ("^name",)
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (
        Recipe.objects.prefetch_related("tags", "ingredients")
        .select_related("author")
        .all()
        # Recipe.objects.all()
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return WriteRecipeSerializer
        return ReadRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        link = request.build_absolute_uri(recipe.get_absolute_url())
        return Response({"short-link": link})

    def get_recipe(self):
        return get_object_or_404(Recipe, pk=self.kwargs.get("pk"))

    @action(
        detail=True,
        methods=["post", "delete"],
    )
    def favorite(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            serializer = FavoriteSerializer(
                data={"user": request.user.pk, "recipe": pk}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)
        favorite = request.user.favorites.filter(recipe=pk)
        if favorite.exists():
            favorite.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            {"errors": InvalidErrorMessage.ALREADY_FAVORITED},
            status=HTTPStatus.BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=["post", "delete"],
    )
    def shopping_cart(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            serializer = ShoppingCartSerializer(
                data={"user": request.user.pk, "recipe": pk}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)
        shopping_cart = request.user.shoppingcarts.filter(recipe=pk)
        if shopping_cart.exists():
            shopping_cart.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            {"errors": InvalidErrorMessage.DUPLICATE_RECIPES},
            status=HTTPStatus.BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=["get"],
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=request.user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        response = HttpResponse(
            content_type="text/csv",
        )
        response["Content-Disposition"] = (
            "attachment; filename=shopping_cart.csv"
        )
        writer = csv.writer(response)
        writer.writerow(["Название", "Единица измерения", "Количество"])
        for ingredient in ingredients:
            writer.writerow(
                [
                    ingredient["ingredient__name"],
                    ingredient["ingredient__measurement_unit"],
                    ingredient["amount"],
                ]
            )
        return response
