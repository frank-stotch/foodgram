from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    TagRecipe,
)


REQUIRED_FIELD_MISSING = "Обязательное поле."


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

    def get_is_subscribed(self, author):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and user.subscribers.filter(author=author).exists()
        )


class UserCreateSerializer(DjoserUserCreateSerializer):

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["__all__"]
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["__all__"]
        read_only_fields = fields


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = (
            "id",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        if not tags:
            raise serializers.ValidationError(REQUIRED_FIELD_MISSING)
        ingredients_data = validated_data.pop("ingredients")
        if not ingredients_data:
            raise serializers.ValidationError(REQUIRED_FIELD_MISSING)
        recipe = Recipe.objects.create(**validated_data)
        TagRecipe.objects.bulk_create(
            [TagRecipe(recipe=recipe, tag=tag) for tag in tags]
        )
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=ingredient["id"],
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients_data
            ]
        )
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        if not ingredients_data:
            raise serializers.ValidationError(REQUIRED_FIELD_MISSING)
        tags = validated_data.pop("tags")
        if not tags:
            raise serializers.ValidationError(REQUIRED_FIELD_MISSING)
        IngredientRecipe.objects.filter(recipe=recipe).exclude(
            id__in=[i["id"] for i in ingredients_data]
        ).delete()
        TagRecipe.objects.filter(recipe=recipe).exclude(
            tag_id__in=[t["id"] for t in tags]
        ).delete()
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=ingredient["id"],
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients_data
            ],
            ignore_conflicts=True,
        )
        TagRecipe.objects.bulk_create(
            [TagRecipe(recipe=recipe, tag=tag) for tag in tags],
            ignore_conflicts=True,
        )
        return super().update(recipe, validated_data)

    def get_is_favorited(self, recipe):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and user.favorites.filter(recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and user.shoppingcarts.filter(recipe=recipe).exists()
        )


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(many=True)
    ingredients = IngredientRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = (
            "id",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, recipe):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and user.favorites.filter(recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and user.shoppingcarts.filter(recipe=recipe).exists()
        )
