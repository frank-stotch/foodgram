from django.utils import timezone


TIME_FORMAT = "%d-%m-%Y %H:%M"


def make_shopping_cart_file(shopping_cart, recipes):
    current_time = timezone.now().strftime(TIME_FORMAT)
    ingredients = [
        f"{index}. {item['ingredient__name'].capitalize()} "
        f"- {item['amount']} "
        f"{item['ingredient__measurement_unit']}"
        for index, item in enumerate(shopping_cart, start=1)
    ]
    recipes = [
        f"{index}. {item.capitalize()}"
        for index, item in enumerate(recipes, start=1)
    ]
    return "\n".join(
        [
            f"Дата и время: {current_time}",
            "",
            "Список покупок:",
            *ingredients,
            "",
            "Список рецептов:",
            *recipes,
        ],
    )
