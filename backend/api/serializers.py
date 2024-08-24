from base64 import b64decode

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    InvalidMessage,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    TagRecipe,
)


REQUIRED_FIELD_MISSING = "Обязательное поле."
DUPLICATE_INGREDIENTS = "Дублирующиеся ингредиенты: {}"
DUPLICATE_TAGS = "Дублирующиеся теги: {}"
DUPLICATE_RECIPES = "Этот рецепт уже есть в списке покупок."


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(use_url=True)

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

    def to_representation(self, user):
        return {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }


class AvatarSerializer(DjoserUserCreateSerializer):
    avatar = Base64ImageField(required=True)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get("avatar")
        instance.save()
        return instance

    def to_representation(self, instance):
        return instance.avatar.url


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


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientRecipeSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True)

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


class WriteRecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(many=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(REQUIRED_FIELD_MISSING)
        unique_ingredients = set()
        duplicates = []
        for ingredient in ingredients:
            if ingredient["amount"] <= 0:
                raise serializers.ValidationError(InvalidMessage.AMOUNT)
            ingredient_id = ingredient.get("id")
            if ingredient_id not in unique_ingredients:
                unique_ingredients.add(ingredient_id)
            else:
                duplicates.append(ingredient_id)
        if duplicates:
            raise serializers.ValidationError(
                DUPLICATE_INGREDIENTS.format(", ".join(duplicates))
            )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(REQUIRED_FIELD_MISSING)
        unique_tags = set()
        duplicates = []
        for tag in tags:
            if tag not in unique_tags:
                unique_tags.add(tag)
            else:
                duplicates.append(tag)
        if duplicates:
            raise serializers.ValidationError(
                DUPLICATE_TAGS.format(", ".join(duplicates))
            )
        return tags

    def validate_image(self, image):
        if self.context.get("request").method == "PATCH" and not image:
            return self.instance.image
        if self.context.get("request").method == "POST" and not image:
            raise serializers.ValidationError(REQUIRED_FIELD_MISSING)
        return image

    @transaction.atomic
    def _save_tags_and_ingredients(self, recipe, tags, ingredients):
        TagRecipe.objects.bulk_create(
            [TagRecipe(tag=tag, recipe=recipe) for tag in tags]
        )
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    ingredient=ingredient,
                    recipe=recipe,
                    amount=ingredient.get("amount"),
                )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        self._save_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = super().update(recipe, validated_data)
        recipe.ingredientrecipes.clear()
        recipe.tags.clear()
        self._save_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    def to_representation(self, recipe):
        return ReadRecipeSerializer(recipe, context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ("user", "recipes")
        read_only_fields = ("user",)
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.select_related(
                    "user", "recipe"
                ).all(),
                fields=("user", "recipe"),
                message=DUPLICATE_RECIPES,
            )
        ]


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        read_only_fields = ("user",)
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.select_related(
                    "user", "recipe"
                ).all(),
                fields=("user", "recipe"),
                message=DUPLICATE_RECIPES,
            )
        ]