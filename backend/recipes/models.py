from django.db import models
from django.contrib.auth.models import AbstractUser
from .validators import validate_username


MAX_LENGTH_EMAIL = 254
MAX_LENGTH_NAME = 256
MAX_LENGTH_SLUG = 50
MAX_LENGTH_USERNAME = 150


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
