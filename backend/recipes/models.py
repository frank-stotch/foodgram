from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.urls import reverse

from .validators import validate_username


class MinValue:
    COOKING_TIME = 1
    AMOUNT = 1


class VerboseName:
    NAME = "Название"
    SLUG = "Идентификатор"
    TAG = "Тег"
    MEASUREMENT_UNIT = "Ед. измерения"
    INGREDIENT = "Продукт"
    AUTHOR = "Автор"
    IMAGE = "Изображение"
    TEXT = "Описание"
    COOKING_TIME = "Время приготовления (в минутах)"
    PUB_DATE = "Дата публикации"
    RECIPE = "Рецепт"
    AMOUNT = "Мера"
    FAVORITE = "Избранное"
    SHOPPING_CART = "Корзина покупок"
    EMAIL = "Эл. почта"
    USERNAME = "Уникальный юзернейм"
    FIRST_NAME = "Имя"
    LAST_NAME = "Фамилия"
    AVATAR = "Фото профиля"
    AUTHOR = "Автор"
    SUBSCRIBER = "Подписчик"
    SUBSCRIPTION = "Подписка"
    USER = "Пользователь"
    RECIPE_INGREDIENT = "Продукт рецепта"


class VerboseNamePlural:
    TAGS = "Теги"
    INGREDIENTS = "Продукты"
    RECIPES = "Рецепты"
    FAVORITES = "Избранные рецепты"
    SHOPPING_CARTS = "Корзины покупок"
    SUBSCRIPTIONS = "Подписки"
    USERS = "Пользователи"
    RECIPE_INGREDIENTS = "Продукты рецепта"


class FieldLength:
    TAG = 32
    INGREDIENT = 128
    MEASUREMENT_UNIT = 64
    RECIPE_NAME = 256
    EMAIL = 254
    USERNAME = 150
    FIRST_NAME = 150
    LAST_NAME = 150


class Error:
    COOKING_TIME = f"Не менее {MinValue.COOKING_TIME} мин. приготовления"
    AMOUNT = f"Не менее {MinValue.AMOUNT} ед. ингредиента"
    ALREADY_IN_SHOPPING_CART = "Рецепт уже есть в списке покупок"
    ALREADY_FAVORITED = "Рецепт уже есть в избранном"
    NOT_IN_SHOPPING_CART = "Рецепта нет в списке покупок"
    NOT_FAVORITED = "Рецепта нет в избранном"
    ALREADY_SUBSCRIBED = "Вы уже подписаны на этого автора"
    CANNOT_SUBSCRIBE_TO_YOURSELF = "Нельзя подписаться на самого себя"
    DUPLICATES = "Дубликаты: {}"
    NO_IMAGE = "Поле 'image' не может быть пустым"
    NOT_SUBSCRIBED = "Вы не подписаны на этого автора"
    NO_TAGS = "Нужен хотя бы один тег"
    NO_INGREDIENTS = "Рецепт не может обойтись без продуктов"


class User(AbstractUser):

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    email = models.EmailField(
        verbose_name=VerboseName.EMAIL,
        max_length=FieldLength.EMAIL,
        unique=True,
    )
    username = models.CharField(
        verbose_name=VerboseName.USERNAME,
        max_length=FieldLength.USERNAME,
        unique=True,
        validators=(validate_username,),
    )
    first_name = models.CharField(
        verbose_name=VerboseName.FIRST_NAME, max_length=FieldLength.FIRST_NAME
    )
    last_name = models.CharField(
        verbose_name=VerboseName.LAST_NAME, max_length=FieldLength.LAST_NAME
    )
    avatar = models.ImageField(
        verbose_name=VerboseName.AVATAR,
        null=True,
        blank=True,
        upload_to=settings.AVATARS_PATH,
    )

    class Meta(AbstractUser.Meta):
        verbose_name = VerboseName.USER
        verbose_name_plural = VerboseNamePlural.USERS
        ordering = ("username",)

    def __str__(self) -> str:
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        to=User,
        verbose_name=VerboseName.SUBSCRIBER,
        related_name="subscribers",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        to=User,
        verbose_name=VerboseName.AUTHOR,
        related_name="authors",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = VerboseName.SUBSCRIPTION
        verbose_name_plural = VerboseNamePlural.SUBSCRIPTIONS
        ordering = ("author",)
        constraints = (
            UniqueConstraint(
                fields=("subscriber", "author"), name="unique_%(class)s"
            ),
        )

    def __str__(self) -> str:
        return f"{self.subscriber} подписан на {self.author}"


class Tag(models.Model):
    name = models.CharField(
        verbose_name=VerboseName.NAME,
        max_length=FieldLength.TAG,
    )

    slug = models.SlugField(
        verbose_name=VerboseName.SLUG,
        max_length=FieldLength.TAG,
        null=True,
        unique=True,
    )

    class Meta:
        verbose_name = VerboseName.TAG
        verbose_name_plural = VerboseNamePlural.TAGS
        default_related_name = "%(class)ss"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name=VerboseName.NAME,
        max_length=FieldLength.INGREDIENT,
    )
    measurement_unit = models.CharField(
        verbose_name=VerboseName.MEASUREMENT_UNIT,
        max_length=FieldLength.MEASUREMENT_UNIT,
    )

    class Meta:
        verbose_name = VerboseName.INGREDIENT
        verbose_name_plural = VerboseNamePlural.INGREDIENTS
        default_related_name = "%(class)ss"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    name = models.CharField(
        verbose_name=VerboseName.NAME,
        max_length=FieldLength.RECIPE_NAME,
    )
    tags = models.ManyToManyField(to=Tag, verbose_name=VerboseNamePlural.TAGS)
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through="RecipeIngredient",
        verbose_name=VerboseNamePlural.INGREDIENTS,
    )
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name=VerboseName.AUTHOR
    )
    image = models.ImageField(
        verbose_name=VerboseName.IMAGE,
        upload_to=settings.RECIPES_IMAGES_PATH,
    )
    text = models.TextField(verbose_name=VerboseName.TEXT)
    cooking_time = models.PositiveIntegerField(
        verbose_name=VerboseName.COOKING_TIME,
        validators=[
            MinValueValidator(
                limit_value=MinValue.COOKING_TIME,
                message=Error.COOKING_TIME,
            )
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name=VerboseName.PUB_DATE, auto_now_add=True
    )

    class Meta:
        verbose_name = VerboseName.RECIPE
        verbose_name_plural = VerboseNamePlural.RECIPES
        default_related_name = "%(class)ss"
        ordering = ("-pub_date",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("recipes:short_link", args=[self.pk])


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name=VerboseName.RECIPE,
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        verbose_name=VerboseName.INGREDIENT,
    )
    amount = models.PositiveIntegerField(
        verbose_name=VerboseName.AMOUNT,
        validators=[
            MinValueValidator(
                limit_value=MinValue.AMOUNT,
                message=Error.AMOUNT,
            )
        ],
    )

    class Meta:
        default_related_name = "%(class)ss"
        ordering = ("recipe", "ingredient")
        constraints = (
            UniqueConstraint(
                fields=("recipe", "ingredient"), name="unique_%(class)s"
            ),
        )
        verbose_name = VerboseName.RECIPE_INGREDIENT
        verbose_name_plural = VerboseNamePlural.RECIPE_INGREDIENTS

    def __str__(self) -> str:
        return f"Ингредиент {self.ingredient} для рецепта {self.recipe}"


class BaseUserRecipeModel(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name=VerboseName.RECIPE,
    )

    class Meta:
        abstract = True
        ordering = ("recipe",)
        default_related_name = "%(class)ss"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_%(class)s",
            ),
        ]


class Favorite(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = VerboseName.FAVORITE
        verbose_name_plural = VerboseNamePlural.FAVORITES


class ShoppingCart(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = VerboseName.SHOPPING_CART
        verbose_name_plural = VerboseNamePlural.SHOPPING_CARTS
