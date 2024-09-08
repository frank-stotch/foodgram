from drf_extra_fields.fields import Base64ImageField
from django.core.validators import MinValueValidator
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.models import (
    Error,
    Favorite,
    Ingredient,
    MinValue,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)


User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, "avatar", "is_subscribed")

    def get_is_subscribed(self, author):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and Subscription.objects.filter(
                author=author, subscriber=user
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


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
                limit_value=MinValue.AMOUNT, message=Error.AMOUNT
            )
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipeingredients", many=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_in_shopping_cart",
            "is_favorited",
        )
        read_only_fields = fields

    @staticmethod
    def _get_favorited_shopping_cart_logic(model, user, recipe):
        return (
            user.is_authenticated
            and model.objects.filter(recipe=recipe, user=user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        return self._get_favorited_shopping_cart_logic(
            ShoppingCart, self.context["request"].user, recipe
        )

    def get_is_favorited(self, recipe):
        return self._get_favorited_shopping_cart_logic(
            Favorite, self.context["request"].user, recipe
        )


class WriteRecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=RecipeIngredientSerializer(),
        allow_empty=False,
        required=True,
    )
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Tag.objects.all(),
        ),
        allow_empty=False,
        required=True,
    )
    image = Base64ImageField(allow_empty_file=False, required=True)

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

    @staticmethod
    def _check_duplicates(array, duplicates_error):
        uniques = set()
        duplicates = set()
        for item in array:
            if item in uniques:
                duplicates.add(item)
            else:
                uniques.add(item)
        if duplicates:
            duplicates = ", ".join(map(str, duplicates))
            raise serializers.ValidationError(
                duplicates_error.format(duplicates)
            )

    def validate_tags(self, tags):
        self._check_duplicates([tag.id for tag in tags], Error.DUPLICATE_TAGS)
        return tags

    def validate_ingredients(self, ingredients):
        self._check_duplicates(
            [item["ingredient"].id for item in ingredients],
            Error.DUPLICATE_INGREDIENTS,
        )
        return ingredients

    @staticmethod
    def _save_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient["ingredient"],
                amount=ingredient["amount"],
            )
            for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
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


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class ReadSubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, "recipes", "recipes_count")

    def get_recipes(self, user):
        request = self.context.get("request")
        recipes_limit = int(request.GET.get("recipes_limit", 10**10))
        return ShortRecipeSerializer(
            user.recipes.all()[:recipes_limit], context=self.context, many=True
        ).data
