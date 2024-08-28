from django.contrib.auth import get_user_model
from django_filters import (
    CharFilter,
    FilterSet,
    ModelChoiceFilter
)

from recipes.models import Ingredient, Recipe


User = get_user_model()


class RecipeFilter(FilterSet):
    is_favorited = CharFilter(method="get_is_favorited")
    is_in_shopping_cart = CharFilter(method="get_is_in_shopping_cart")
    author = ModelChoiceFilter(queryset=User.objects.all())
    tags = CharFilter(method='filter_tags')

    class Meta:
        model = Recipe
        fields = ["is_favorited", "is_in_shopping_cart", "author", "tags"]

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorites__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(shoppingcarts__user=user)
        return queryset

    def filter_tags(self, queryset, name, value):
        tag_slugs = self.request.GET.getlist('tags')
        return queryset.filter(tags__slug__in=tag_slugs).distinct()


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith', field_name='name')

    class Meta:
        model = Ingredient
        fields = ['name']
