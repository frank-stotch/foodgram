from http import HTTPStatus

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from . import filters, permissions, serializers
from recipes.models import Ingredient, Recipe, Tag


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
            if serializer.is_valid():
                user.avatar = serializer.validated_data["avatar"]
                user.save()
                return Response(
                    serializers.AvatarSerializer(user).data,
                    status=HTTPStatus.OK,
                )
            return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)
        user.avatar.delete(save=True)
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
    permission_classes = (permissions.IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilterSet

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return serializers.ReadRecipeSerializer
        return serializers.WriteRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        link = request.build_absolute_uri(recipe.get_absolute_url())
        return Response({"short-link": link}, status=HTTPStatus.OK)
