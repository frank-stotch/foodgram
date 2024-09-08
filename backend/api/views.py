from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from . import filters, pagination, permissions, serializers, utils
from recipes.models import (
    Error,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    ShoppingCart,
    Tag,
)


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    def get_permissions(self):
        if self.action == "me":
            return (IsAuthenticated(),)
        if self.action == "retrieve":
            return (AllowAny(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=("put", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = serializers.AvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.avatar = serializer.validated_data["avatar"]
            user.save()
            return Response(
                serializers.AvatarSerializer(user).data,
                status=HTTPStatus.OK,
            )
        user.avatar.delete(save=True)
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=False,
        methods=("GET",),
        pagination_class=pagination.LimitPageNumberPagination,
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(authors__subscriber=request.user)
        serializer = serializers.ReadSubscriptionSerializer(
            self.paginate_queryset(queryset),
            many=True,
            context={"request": request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=(
            "POST",
            "DELETE",
        ),
    )
    def subscribe(self, request, id):
        subscriber = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == "POST":
            if author == subscriber:
                return Response(
                    dict(errors=Error.CANNOT_SUBSCRIBE_TO_YOURSELF),
                    status=HTTPStatus.BAD_REQUEST,
                )
            if Subscription.objects.filter(
                author=author, subscriber=subscriber
            ).exists():
                return Response(
                    dict(errors=Error.ALREADY_SUBSCRIBED),
                    status=HTTPStatus.BAD_REQUEST,
                )
            Subscription.objects.create(author=author, subscriber=subscriber)
            return Response(
                serializers.ReadSubscriptionSerializer(
                    author, context={"request": request}
                ).data,
                status=HTTPStatus.CREATED,
            )
        get_object_or_404(
            Subscription, author=author, subscriber=subscriber
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    pagination_class = None
    filter_backends = (filters.IngredientFilter,)
    search_fields = ("^name",)
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (permissions.IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilterSet

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return serializers.ReadRecipeSerializer
        return serializers.WriteRecipeSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.method == "PATCH":
            kwargs["partial"] = False
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, url_path="get-link")
    def get_link(self, request, pk=None):
        return Response(
            {
                "short-link": request.build_absolute_uri(
                    self.get_object().get_absolute_url()
                )
            },
            status=HTTPStatus.OK,
        )

    @action(detail=False)
    def download_shopping_cart(self, request):
        shopping_cart = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=request.user
            )
            .values(
                "ingredient__name",
                "ingredient__measurement_unit",
            )
            .annotate(amount=Sum("amount"))
            .order_by("ingredient__name")
        )
        unique_recipes = (
            ShoppingCart.objects.filter(user=request.user)
            .values_list("recipe__name", flat=True)
            .distinct()
        )
        return utils.make_shopping_cart_file(shopping_cart, unique_recipes)

    @staticmethod
    def _favorite_shopping_cart_logic(
        request,
        error_message_add,
        error_message_delete,
        pk,
        model,
    ):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            item, created = model.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                return Response(
                    serializers.ShortRecipeSerializer(recipe).data,
                    status=HTTPStatus.CREATED,
                )
            return Response(
                dict(error=error_message_add),
                status=HTTPStatus.BAD_REQUEST,
            )
        if model.objects.filter(recipe=recipe, user=request.user).exists():
            model.objects.filter(recipe=recipe, user=request.user).delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            dict(error=error_message_delete),
            status=HTTPStatus.BAD_REQUEST,
        )

    @action(detail=True, methods=("POST", "DELETE"))
    def favorite(self, request, pk):
        return self._favorite_shopping_cart_logic(
            request,
            error_message_add=Error.ALREADY_FAVORITED,
            error_message_delete=Error.NOT_FAVORITED,
            pk=pk,
            model=Favorite,
        )

    @action(detail=True, methods=("POST", "DELETE"))
    def shopping_cart(self, request, pk):
        return self._favorite_shopping_cart_logic(
            request,
            error_message_add=Error.ALREADY_IN_SHOPPING_CART,
            error_message_delete=Error.NOT_IN_SHOPPING_CART,
            pk=pk,
            model=ShoppingCart,
        )
