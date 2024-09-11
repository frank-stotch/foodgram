from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.html import format_html, format_html_join
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
        user_queryset = user_queryset.annotate(recipe_count=Count('recipes'))
        if self.value() == "yes":
            return user_queryset.filter(recipe_count__gt=0)
        if self.value() == "no":
            return user_queryset.filter(recipe_count=0)
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
        user_queryset = user_queryset.annotate(
            subscription_count=Count("subscribers", distinct=True)
        )
        if self.value() == "yes":
            return user_queryset.filter(subscription_count__gt=0)
        if self.value() == "no":
            return user_queryset.filter(subscription_count=0)
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
        user_queryset = user_queryset.annotate(
            subscriber_count=Count("authors", distinct=True)
        )
        if self.value() == "yes":
            return user_queryset.filter(subscriber_count__gt=0)
        if self.value() == "no":
            return user_queryset.filter(subscriber_count=0)
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
    def avatar_display(self, obj):
        if obj.avatar:
            return format_html(
                (
                    '<a href="{}" target="_blank">'
                    '<img src="{}" width="100" height="100" '
                    'style="object-fit: cover;" />'
                    "</a>"
                ),
                obj.avatar.url,
                obj.avatar.url,
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


class RecipeAuthorFilter(admin.SimpleListFilter):
    title = "Автор"
    parameter_name = "author"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request).select_related("author")
        if (
            settings.DATABASES["default"]["ENGINE"]
            == "django.db.backends.postgresql"
        ):
            authors = qs.values_list(
                "author__id", "author__username"
            ).distinct("author__id")
        else:
            authors = set(
                (recipe.author.id, recipe.author.username) for recipe in qs
            )
        return [(author_id, username) for author_id, username in authors]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(author__id=self.value())
        return queryset


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
        RecipeAuthorFilter,
    )
    search_fields = ("name", "tags__name", "ingredients__name")

    def get_queryset(self, request):
        queryset = (
            super()
            .get_queryset(request)
            .select_related("author")
            .prefetch_related(
                "tags", "ingredients", "recipeingredients__ingredient"
            )
        )

        if (
            settings.DATABASES["default"]["ENGINE"]
            == "django.db.backends.postgresql"
        ):
            return queryset.annotate(
                count_in_favorite=Count("favorites", distinct=True)
            )
        return queryset.annotate(count_in_favorite=Count("favorites"))

    @admin.display(description="В избранном")
    def count_in_favorite(self, recipe):
        return recipe.count_in_favorite

    @admin.display(description="Изображение")
    def image_display(self, obj):
        if obj.image:
            image_url = obj.image.url
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="100" height="100" '
                'style="object-fit: cover;" />'
                "</a>",
                image_url,
                image_url,
            )
        return "-"

    @admin.display(description="Ингредиенты")
    def ingredients_list(self, obj):
        ingredient_lines = [
            (
                f"{recipe_ingredient.ingredient.name} - "
                f"{recipe_ingredient.amount} "
                f"{recipe_ingredient.ingredient.measurement_unit}"
            )
            for recipe_ingredient in obj.recipeingredients.select_related(
                "ingredient"
            )
        ]
        return format_html("<br>".join(ingredient_lines))

    @admin.display(description="Теги")
    def tags_list(self, obj):
        tags = obj.tags.all()
        return format_html_join(
            "",
            '<div style="margin-bottom: 4px;">{}</div>',
            ((tag.name,) for tag in tags),
        )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = list_display


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = list_display
