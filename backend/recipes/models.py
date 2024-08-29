from django.urls import reverse

from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator

from .constants import InvalidMessage, HelpText, MaxLength, Minimum


User = get_user_model()


class BaseNameModel(models.Model):
    name = models.CharField(
        verbose_name="Название",
        max_length=MaxLength.NAME,
        help_text=HelpText.NAME,
    )

    class Meta:
        abstract = True
        ordering = ("name",)
        default_related_name = "%(class)ss"


class Tag(BaseNameModel):
    slug = models.SlugField(
        verbose_name="Идентификатор",
        max_length=MaxLength.SLUG,
        unique=True,
        help_text=HelpText.SLUG,
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Ingredient(BaseNameModel):
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        max_length=MaxLength.UNIT,
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Recipe(BaseNameModel):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="recipes",
    )
    image = models.ImageField(
        verbose_name="Изображение",
        upload_to="recipes/images",
    )
    text = models.TextField(verbose_name="Описание")
    tags = models.ManyToManyField(
        to=Tag, through="RecipeTag", verbose_name="Теги"
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления в минутах",
        validators=[
            MinValueValidator(
                limit_value=Minimum.COOKING_TIME,
                message=InvalidMessage.COOKING_TIME,
            )
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True
    )
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through="RecipeIngredient",
        verbose_name="Ингредиенты",
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)

    def get_absolute_url(self):
        return reverse("short_link", args=[self.pk])


class BaseRecipeModel(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        abstract = True
        default_related_name = "%(class)ss"


class RecipeTag(BaseRecipeModel):
    tag = models.ForeignKey(
        to=Tag, on_delete=models.CASCADE, verbose_name="Тег"
    )

    class Meta(BaseRecipeModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "tag"], name="only_unique_tags"
            ),
        ]
        ordering = ("recipe",)


class RecipeIngredient(BaseRecipeModel):
    ingredient = models.ForeignKey(
        to=Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(
                limit_value=Minimum.AMOUNT,
                message=InvalidMessage.AMOUNT,
            )
        ],
    )

    class Meta(BaseRecipeModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="only_unique_ingredients"
            ),
        ]


class BaseUserRecipeModel(BaseRecipeModel):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    class Meta(BaseRecipeModel.Meta):
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_%(class)s",
            ),
        ]


class Favorite(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = verbose_name


class ShoppingCart(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = "Корзина покупок"
        verbose_name_plural = verbose_name
