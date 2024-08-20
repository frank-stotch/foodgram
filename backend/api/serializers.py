from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)
from rest_framework import serializers

from recipes.models import Subscription


User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "first_name",
            "last_name",
            "username",
            "avatar",
            "is_subscribed",
        )

    def get_is_subscribed(self, subscriber):
        author_pk = self.context.get("request").kwargs.get("id")
        return Subscription.objects.filter(
            author__pk=author_pk, subscriber=subscriber
        ).exists()


class UserCreateSerializer(DjoserUserCreateSerializer):

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password")
