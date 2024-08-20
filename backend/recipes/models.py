from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from .validators import validate_username


MIN_AMOUNT = 1
MIN_COOKING_TIME = 1
MAX_LENGTH_EMAIL = 254
MAX_LENGTH_NAME = 256
MAX_LENGTH_SLUG = 50
MAX_LENGTH_USERNAME = 150
MAX_UNIT_LENGTH = 16

INVALID_AMOUNT = f"Хотя бы {MIN_AMOUNT} ед. выбранного ингредиента!"
INVALID_COOKING_TIME = f"Хотя бы {MIN_COOKING_TIME} мин. готовки!"


class HelpText:
    NAME = f"Не более {MAX_LENGTH_NAME} символов"
    SLUG = f"Не более {MAX_LENGTH_SLUG} символов. Обязан быть уникальным"
    USERNAME = (
        f"Максимум {MAX_LENGTH_USERNAME} символов. Допускаются "
        "буквы, цифры и символы @/./+/- ."
    )


class User(AbstractUser):
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=MAX_LENGTH_USERNAME,
        help_text=HelpText.USERNAME,
        unique=True,
        validators=[
            validate_username,
        ],
    )
    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
    )
    avatar = models.ImageField(
        upload_to="users/",
        verbose_name="Фото профиля",
        null=True,
        default=None,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)


class BaseNameModel(models.Model):
    name = models.CharField(
        verbose_name="Название",
        max_length=MAX_LENGTH_NAME,
        help_text=HelpText.NAME,
        unique=True,
    )

    class Meta:
        abstract = True
        ordering = ("name",)
        default_related_name = "%(class)ss"


class Tag(BaseNameModel):
    slug = models.SlugField(
        verbose_name="Идентификатор",
        max_length=MAX_LENGTH_SLUG,
        unique=True,
        help_text=HelpText.SLUG,
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Ingredient(BaseNameModel):
    unit = models.CharField(
        verbose_name="Единица измерения",
        max_length=MAX_UNIT_LENGTH,
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Recipe(BaseNameModel):
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name="Автор"
    )
    image = models.ImageField(upload_to="recipes/images")
    text = models.TextField(verbose_name="Описание")
    tag = models.ManyToManyField(to=Tag)
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления в минутах",
        validators=[
            MinValueValidator(
                limit_value=MIN_COOKING_TIME, message=INVALID_COOKING_TIME
            )
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="ingredient",
    )
    ingredient = models.ForeignKey(
        to=Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(limit_value=MIN_AMOUNT, message=INVALID_AMOUNT),
        ],
    )

    class Meta:
        ordering = ("recipe", "ingredient")
        default_related_name = "%(class)ss"


class BaseUserRecipeModel(models.Model):
    user = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name="Автор"
    )
    recipe = models.ForeignKey(
        to=Recipe, on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        abstract = True
        ordering = ("user", "recipe")
        default_related_name = "%(class)ss"


class Favorite(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"


class Subscription(models.Model):
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="authors"
    )
    subscriber = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="subscribers"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ("subscriber", "author")
        unique_together = ("author", "subscriber")
        constraints = [
            models.CheckConstraint(
                check=~models.Q(author=models.F("subscriber")),
                name="you_cant_subscribe_to_yourself",
            )
        ]


class ShoppingList(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="you already have this recipe on the list",
            )
        ]
