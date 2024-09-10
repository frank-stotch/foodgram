from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.html import format_html, format_html_join
from rest_framework.authtoken.models import TokenProxy

from .models import (
    Favorite,
    Ingredient,
    MinValue,
    Recipe,
    RecipeIngredient,
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

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(recipes__isnull=True)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "С подписками"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(subscribers__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(subscribers__isnull=True)
        return queryset


class HasSubscribersFilter(admin.SimpleListFilter):
    title = "С подписчиками"
    parameter_name = "has_subscribers"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(authors__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(authors__isnull=True)
        return queryset


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

    @admin.display(description="Количество подписчиков")
    def subscribers_count(self, obj):
        return obj.subscribers_count

    @admin.display(description="Количество подписок")
    def subscriptions_count(self, obj):
        return obj.subscriptions_count

    @admin.display(description="Количество рецептов")
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

    @admin.display(description="Число рецептов")
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

    @admin.display(description="Число рецептов")
    def recipes_count(self, obj):
        return obj.recipes_count


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    min_num = MinValue.AMOUNT


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
    list_filter = ("tags",)

    @admin.display(description="Счетчик в избранном")
    def count_in_favorite(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Изображение')
    def image_display(self, obj):
        if obj.image:
            image_url = obj.image.url
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="100" height="100" '
                'style="object-fit: cover;" />'
                '</a>',
                image_url,
                image_url
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
            '',
            '<div style="margin-bottom: 4px;">{}</div>',
            ((tag.name,) for tag in tags)
        )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = list_display


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = list_display
