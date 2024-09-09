from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.html import format_html
from rest_framework.authtoken.models import TokenProxy

from .models import Subscription, User, Recipe

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
    ) + readonly_fields
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("id",)

    # Переопределяем метод get_queryset для добавления аннотаций
    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                subscribers_count=Count("authors", distinct=True),
                subscriptions_count=Count("subscribers", distinct=True),
                recipes_count=Count("recipes", distinct=True),
            )
        )

    # Используем аннотированные значения
    def subscribers_count(self, obj):
        return obj.subscribers_count

    subscribers_count.short_description = "Количество подписчиков"

    def subscriptions_count(self, obj):
        return obj.subscriptions_count

    subscriptions_count.short_description = "Количество подписок"

    def recipes_count(self, obj):
        return obj.recipes_count

    recipes_count.short_description = "Количество рецептов"

    @admin.display(description="Аватар")
    def avatar_display(self, obj):
        if obj.avatar:
            return format_html(
                (
                    '<img src="{}" width="50" height="50" '
                    'style="object-fit: cover;" />'
                ),
                obj.avatar.url,
            )
        return "-"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "author")
