from django.db import models


class VerboseName:
    NAME = "Название"
    SLUG = "Идентификатор"
    TAG = "Тег"
    MEASUREMENT_UNIT = "Ед. измерения"
    INGREDIENT = "Ингредиент"


class FieldLength:
    TAG = 32
    INGREDIENT = 128
    MEASUREMENT_UNIT = 64


class BaseNameModel(models.Model):
    name = models.CharField(
        verbose_name=VerboseName.NAME,
        max_length=FieldLength.TAG,
    )

    class Meta:
        abstract = True
        default_related_name = "%(class)ss"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


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
        verbose_name_plural = verbose_name + "и"
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
        max_length=FieldLength.MEASUREMENT_UNIT
    )

    class Meta:
        verbose_name = VerboseName.INGREDIENT
        verbose_name_plural = verbose_name + "ы"
        default_related_name = "%(class)ss"
        ordering = ("name",)

    def __str__(self):
        return self.name
