from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.urls import reverse


User = get_user_model()


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


class VerboseNamePlural:
    TAGS = "Теги"
    INGREDIENTS = "Продукты"
    RECIPES = "Рецепты"


class FieldLength:
    TAG = 32
    INGREDIENT = 128
    MEASUREMENT_UNIT = 64
    RECIPE_NAME = 256


class Error:
    COOKING_TIME = f"Не менее {MinValue.COOKING_TIME} мин. приготовления"
    AMOUNT = f"Не менее {MinValue.AMOUNT} ед. ингредиента"
    ALREADY_IN_SHOPPING_CART = "Рецепт уже есть в списке покупок"
    ALREADY_FAVORITED = "Рецепт уже есть в избранном"
    NOT_IN_SHOPPING_CART = "Рецепта нет в списке покупок"
    NOT_FAVORITED = "Рецепта нет в избранном"


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
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        verbose_name=VerboseName.NAME,
        max_length=FieldLength.RECIPE_NAME,
    )
    tags = models.ManyToManyField(
        to=Tag, verbose_name=VerboseNamePlural.TAGS
    )
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
        return reverse("short_link", args=[str(self.pk)])


class BaseRecipeModel(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name=VerboseName.RECIPE,
    )

    class Meta:
        abstract = True
        default_related_name = "%(class)ss"
        ordering = ("recipe",)


class RecipeIngredient(BaseRecipeModel):
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

    class Meta(BaseRecipeModel.Meta):
        constraints = (
            UniqueConstraint(
                fields=("recipe", "ingredient"), name="unique_%(class)s"
            ),
        )

    def __str__(self) -> str:
        return f"Ингредиент {self.ingredient} для рецепта {self.recipe}"


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
        verbose_name = VerboseName.FAVORITE
        verbose_name_plural = verbose_name


class ShoppingCart(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = "Корзина покупок"
        verbose_name_plural = verbose_name
