from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.constraints import UniqueConstraint

from .validators import validate_username


class VerboseName:
    EMAIL = "Эл. почта"
    USERNAME = "Имя пользователя"
    FIRST_NAME = "Имя"
    LAST_NAME = "Фамилия"
    AVATAR = "Фото профиля"
    AUTHOR = "Автор"
    SUBSCRIBER = "Подписчик"
    SUBSCRIPTION = "Подписки"


class FieldLength:
    EMAIL = 254
    STANDARD = 150


class Error:
    ALREADY_SUBSCRIBED = "Вы уже подписаны на этого автора"
    CANNOT_SUBSCRIBE_TO_YOURSELF = "Нельзя подписаться на самого себя"


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
        max_length=FieldLength.STANDARD,
        unique=True,
        validators=(validate_username,),
    )
    first_name = models.CharField(
        verbose_name=VerboseName.FIRST_NAME, max_length=FieldLength.STANDARD
    )
    last_name = models.CharField(
        verbose_name=VerboseName.FIRST_NAME, max_length=FieldLength.STANDARD
    )
    avatar = models.ImageField(
        verbose_name=VerboseName.AVATAR,
        null=True,
        blank=True,
        upload_to="users/avatars/",
    )

    class Meta(AbstractUser.Meta):
        ordering = ("username",)

    def __str__(self) -> str:
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        to=User,
        verbose_name=VerboseName.SUBSCRIBER,
        related_name="subscriber",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        to=User,
        verbose_name=VerboseName.AUTHOR,
        related_name="subscribing",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = VerboseName.SUBSCRIPTION
        verbose_name_plural = verbose_name
        ordering = ("author",)
        constraints = (
            UniqueConstraint(
                fields=("subscriber", "author"), name="unique_%(class)s"
            ),
        )

    def __str__(self) -> str:
        return f"{self.subscriber} подписан на {self.author}"
