from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import HelpText, MaxLength
from .validators import validate_username


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
        help_text=HelpText.PASSWORD,
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

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "username",
        "first_name",
        "last_name",
    ]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="subscribed_to",
        verbose_name="Автор",
    )
    subscriber = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Подписчик",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["author", "subscriber"],
                name="you_cannot_subscribe_to_yourself",
            ),
        ]

    def __str__(self):
        return f"{self.subscriber} подписан на {self.author}"
