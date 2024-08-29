from base64 import b64decode
from string import digits

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
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
    InvalidMessage,
    Minimum,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription
from .constants import InvalidErrorMessage


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


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
        # read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit",
    )
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(
                limit_value=Minimum.AMOUNT, message=InvalidMessage.AMOUNT
            )
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")
        read_only_fields = fields


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(many=True)
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


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class WriteRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=True
    )
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

    def validate(self, data):
        tags = data.get("tags")
        ingredients = data.get("ingredients")
        if not ingredients:
            raise serializers.ValidationError(
                dict(ingredients="Должен быть хотя бы 1 ингредиент.")
            )
        if not tags:
            raise serializers.ValidationError(
                dict(tags="Должен быть хотя бы 1 тег.")
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                "Дублирование в тэгах недопустимо."
            )
        ingredients_ids = [item["ingredient"].id for item in ingredients]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться"
            )
        return super().validate(data)

    @transaction.atomic
    def _save_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                ingredient=ingredient.get("ingredient"),
                recipe=recipe,
                amount=ingredient.get("amount"),
            )
            for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        new_ingredients = validated_data.pop("ingredients")
        recipe.tags.clear()
        recipe.ingredients.clear()
        self._save_ingredients(recipe, new_ingredients)
        return super().update(recipe, validated_data)

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
                message=InvalidErrorMessage.DUPLICATE_RECIPES,
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
                message=InvalidErrorMessage.ALREADY_FAVORITED,
            )
        ]


class ReadSubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, user):
        request = self.context.get("request")
        recipes_limit = request.GET.get("recipes_limit")
        recipes = user.recipes.all()
        if recipes_limit and recipes_limit in digits:
            recipes = recipes[: int(recipes_limit)]
        serializer = ShortRecipeSerializer(
            recipes, context=self.context, many=True
        )
        return serializer.data


class WriteSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ("author", "subscriber")

    def validate(self, data):
        subscriber = data.get("subscriber")
        author = data.get("author")
        if author == subscriber:
            raise serializers.ValidationError(
                InvalidErrorMessage.CANNOT_SUBSCRIBE_TO_YOURSELF
            )
        if Subscription.objects.filter(
            author=author, subscriber=subscriber
        ).exists():
            raise serializers.ValidationError(
                InvalidErrorMessage.ALREADY_SUBSCRIBED
            )
        return data

    def to_representation(self, instance):
        return ReadSubscriptionSerializer(
            instance.author, context=self.context
        ).data
