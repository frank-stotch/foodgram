from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from .validators import validate_username


class Minimum:
    AMOUNT = 1
    COOKING_TIME = 1


class MaxLength:
    EMAIL = 254
    NAME = 256
    SLUG = 50
    USERNAME = 150
    UNIT = 16
    ANTHROPONYM = 150
    PASSWORD = 128


class HelpText:
    NAME = f"Не более {MaxLength.EMAIL} символов"
    SLUG = f"Не более {MaxLength.SLUG} символов. Обязан быть уникальным"
    USERNAME = (
        f"Максимум {MaxLength.USERNAME} символов. Допускаются "
        "буквы, цифры и символы @/./+/- ."
    )


class InvalidMessage:
    AMOUNT = f"Хотя бы {Minimum.AMOUNT} ед. выбранного ингредиента!"
    COOKING_TIME = f"Хотя бы {Minimum.COOKING_TIME} мин. готовки!"


class User(AbstractUser):
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=MaxLength.USERNAME,
        help_text=HelpText.USERNAME,
        unique=True,
        validators=[
            validate_username,
        ],
        null=False,
        blank=False,
    )
    password = models.CharField(
        verbose_name="Пароль",
        null=False,
        blank=False,
        max_length=MaxLength.PASSWORD,
    )
    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=MaxLength.EMAIL,
        unique=True,
        null=False,
        blank=False,
    )
    avatar = models.ImageField(
        upload_to="users/",
        verbose_name="Фото профиля",
        null=True,
        default=None,
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=MaxLength.ANTHROPONYM,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=MaxLength.ANTHROPONYM,
        blank=False,
        null=False,
    )

    REQUIRED_FIELDS = [
        "username",
        "password",
        "email",
        "first_name",
        "last_name",
    ]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class BaseNameModel(models.Model):
    name = models.CharField(
        verbose_name="Название",
        max_length=MaxLength.NAME,
        help_text=HelpText.NAME,
        unique=True,
    )

    class Meta:
        abstract = True
        ordering = ("name",)
        default_related_name = "%(class)ss"

    def __str__(self):
        return self.name


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
        to=User, on_delete=models.CASCADE, verbose_name="Автор"
    )
    image = models.ImageField(
        verbose_name="Изображение", upload_to="recipes/images"
    )
    text = models.TextField(verbose_name="Описание")
    tag = models.ManyToManyField(
        to=Tag, through="TagRecipe", verbose_name="Тег"
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
        to=Ingredient, through="IngredientRecipe"
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)


class TagRecipe(models.Model):
    tag = models.ForeignKey(to=Tag, on_delete=models.SET_NULL)
    recipe = models.ForeignKey(to=Recipe, on_delete=models.CASCADE)

    class Meta:
        default_related_name = "%(class)ss"
        constraints = [
            models.UniqueConstraint(
                fields=["tag", "recipe"], name="you_already_have_this_tag"
            )
        ]


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        to=Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(
                limit_value=Minimum.AMOUNT,
                message=InvalidMessage.COOKING_TIME,
            ),
        ],
    )

    class Meta:
        ordering = ("recipe", "ingredient")
        default_related_name = "%(class)ss"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="you_already_have_this_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.recipe} {self.ingredient} {self.amount}"


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

    def __str__(self):
        return f"{self.user} {self.recipe}"


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
        constraints = [
            models.UniqueConstraint(
                fields=["author", "subscriber"],
                name="you_already_have_this_subscription",
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F("subscriber")),
                name="you_can't_subscribe_to_yourself",
            ),
        ]

    def __str__(self):
        return f"{self.subscriber} {self.author}"


class ShoppingCart(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="you already have this recipe on the list",
            )
        ]
