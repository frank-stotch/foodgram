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

INVALID_AMOUNT = f'Хотя бы {MIN_AMOUNT} ед. выбранного ингредиента!'
INVALID_COOKING_TIME = f'Хотя бы {MIN_COOKING_TIME} мин. готовки!'


class Role(models.TextChoices):
    user = ('user', 'Пользователь')
    admin = ('admin', 'Администратор')


class HelpText:
    NAME = f'Не более {MAX_LENGTH_NAME} символов'
    SLUG = (
        f'Не более {MAX_LENGTH_SLUG} символов. Обязан быть уникальным'
    )
    USERNAME = (
        f'Максимум {MAX_LENGTH_USERNAME} символов. Допускаются '
        'буквы, цифры и символы @/./+/- .'
    )


class User(AbstractUser):
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_LENGTH_USERNAME,
        help_text=HelpText.USERNAME,
        unique=True,
        validators=[
            validate_username,
        ],
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=max(len(choice) for choice in list(Role)),
        choices=Role.choices,
        default=Role.user,
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=MAX_LENGTH_EMAIL,
        unique=True
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        verbose_name='Аватар',
        null=True,
        default=None
    )

    @property
    def is_admin(self):
        return self.role == Role.admin or self.is_staff

    class Meta:
        ordering = ('username',)


class BaseNameModel(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME,
        help_text=HelpText.NAME,
    )

    class Meta:
        abstract = True
        ordering = ('name',)
        default_related_name = '%(class)ss'


class Tag(BaseNameModel):
    slug = models.SlugField(
        verbose_name='Идентификатор',
        max_length=MAX_LENGTH_SLUG,
        unique=True,
        help_text=HelpText.SLUG,
    )


class Ingredient(BaseNameModel):
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_UNIT_LENGTH,
    )


class Recipe(BaseNameModel):
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    image = models.ImageField(upload_to='recipes/images')
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through='IngredientRecipe',
    )
    tag = models.ManyToManyField(to=Tag)
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MinValueValidator(
                limit_value=MIN_COOKING_TIME,
                message=INVALID_COOKING_TIME
            )
        ]
    )


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(limit_value=MIN_AMOUNT, message=INVALID_AMOUNT),
        ]
    )
