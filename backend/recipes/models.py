from django.db import models


class VerboseName:
    NAME = "Название"
    SLUG = "Идентификатор"
    TAG = "Тег"


class FieldLength:
    TAG = 32


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


class Tag(BaseNameModel):
    slug = models.SlugField(
        verbose_name=VerboseName.SLUG,
        max_length=FieldLength.TAG,
        null=True,
        unique=True,
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = VerboseName.TAG
        verbose_name_plural = verbose_name + "и"


