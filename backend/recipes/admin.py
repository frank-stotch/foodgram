from django.contrib import admin
from django.utils.html import format_html

from .models import User, Subscription, Recipe


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 0


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    fk_name = "subscriber"
    extra = 0
    verbose_name = "Подписка на автора"
    verbose_name_plural = "Подписки на авторов"


class SubscriberInline(admin.TabularInline):
    model = Subscription
    fk_name = "author"
    extra = 0
    verbose_name = "Подписчик"
    verbose_name_plural = "Подписчики"


class HasRecipesFilter(admin.SimpleListFilter):
    title = "С рецептами"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть рецепты"),
            ("no", "Нет рецептов"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(recipes__isnull=True).distinct()


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "С подписками"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть подписки"),
            ("no", "Нет подписок"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(subscribers__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(subscribers__isnull=True).distinct()


class HasSubscribersFilter(admin.SimpleListFilter):
    title = "С подписчиками"
    parameter_name = "has_subscribers"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть подписчики"),
            ("no", "Нет подписчиков"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(authors__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(authors__isnull=True).distinct()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "avatar_display",
        "recipe_count",
        "subscription_count",
        "subscriber_count",
    )
    search_fields = ("username", "email")
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
    )
    inlines = [RecipeInline, SubscriptionInline, SubscriberInline]

    def avatar_display(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:50%;" />',
                obj.avatar.url,
            )
        return "-"

    avatar_display.short_description = "Аватар"

    def recipe_count(self, obj):
        return obj.recipes.count()

    recipe_count.short_description = "Число рецептов"

    def subscription_count(self, obj):
        return obj.subscribers.count()

    subscription_count.short_description = "Число подписок"

    def subscriber_count(self, obj):
        return obj.authors.count()

    subscriber_count.short_description = "Число подписчиков"
