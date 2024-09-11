from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import TokenProxy

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)

admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


class HasRecipesFilter(admin.SimpleListFilter):
    title = "С рецептами"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, user_queryset):
        if self.value() == "yes":
            return user_queryset.filter(recipes_count__gt=0)
        if self.value() == "no":
            return user_queryset.filter(recipes_count=0)
        return user_queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "С подписками"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, user_queryset):
        if self.value() == "yes":
            return user_queryset.filter(subscriptions_count__gt=0)
        if self.value() == "no":
            return user_queryset.filter(subscriptions_count=0)
        return user_queryset


class HasSubscribersFilter(admin.SimpleListFilter):
    title = "С подписчиками"
    parameter_name = "has_subscribers"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, user_queryset):
        if self.value() == "yes":
            return user_queryset.filter(subscribers_count__gt=0)
        if self.value() == "no":
            return user_queryset.filter(subscribers_count=0)
        return user_queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    readonly_fields = (
        "subscribers_count",
        "subscriptions_count",
        "recipes_count",
    )
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "avatar_display",
        *readonly_fields,
    )
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("id",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("authors", "subscribers", "recipes")
            .annotate(
                subscribers_count=Count("authors", distinct=True),
                subscriptions_count=Count("subscribers", distinct=True),
                recipes_count=Count("recipes", distinct=True),
            )
        )

    @admin.display(description="Подписчики")
    def subscribers_count(self, obj):
        return obj.subscribers_count

    @admin.display(description="Подписки")
    def subscriptions_count(self, obj):
        return obj.subscriptions_count

    @admin.display(description="Рецепты")
    def recipes_count(self, obj):
        return obj.recipes_count

    @admin.display(description="Аватар")
    @mark_safe
    def avatar_display(self, user):
        if user.avatar:
            return (
                f'<a href="{user.avatar.url}" target="_blank">'
                f'<img src="{user.avatar.url}" width="100" height="100" '
                'style="object-fit: cover;" />'
                "</a>"
            )
        return "-"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "author")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "recipes_count")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_count=Count("recipes__tags", distinct=True)
        )

    @admin.display(description="Рецепты")
    def recipes_count(self, obj):
        return obj.recipes_count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit", "recipes_count")
    list_filter = ("measurement_unit",)
    search_fields = ("name",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_count=Count("recipeingredients__recipe", distinct=True)
        )

    @admin.display(description="Рецепты")
    def recipes_count(self, obj):
        return obj.recipes_count


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = ("count_in_favorite",)
    list_display = (
        "name",
        "author",
        "image_display",
        "text",
        "cooking_time",
        "count_in_favorite",
        "tags_list",
        "ingredients_list",
    )
    list_filter = (
        "tags",
        "author",
    )
    search_fields = ("name", "tags__name", "ingredients__name")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("author")
            .prefetch_related(
                "tags", "ingredients", "recipeingredients__ingredient"
            )
            .annotate(count_in_favorite=Count("favorites"))
        )

    @admin.display(description="В избранном")
    def count_in_favorite(self, recipe):
        return recipe.count_in_favorite

    @admin.display(description="Изображение")
    @mark_safe
    def image_display(self, recipe):
        if recipe.image:
            return (
                f'<a href="{recipe.image.url}" target="_blank">'
                f'<img src="{recipe.image.url}" width="100" height="100" '
                'style="object-fit: cover;" />'
                "</a>"
            )
        return "-"

    @admin.display(description="Ингредиенты")
    @mark_safe
    def ingredients_list(self, recipe):
        return "<br>".join(
            [
                f"{recipe_ingredient.ingredient.name} - "
                f"{recipe_ingredient.amount} "
                f"{recipe_ingredient.ingredient.measurement_unit}"
                for recipe_ingredient
                in recipe.recipeingredients.select_related(
                    "ingredient"
                )
            ]
        )

    @admin.display(description="Теги")
    @mark_safe
    def tags_list(self, recipe):
        tags = recipe.tags.all()
        return "<br>".join([tag.name for tag in tags])


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = list_display


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = list_display
