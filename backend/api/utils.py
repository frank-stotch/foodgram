from django.http import FileResponse
from django.utils import timezone


TIME_FORMAT = "%d-%m-%Y %H:%M"


def make_shopping_cart_file(shopping_cart, unique_recipes):
    current_time = timezone.now().strftime(TIME_FORMAT)
    ingredients = []
    recipes = []
    for index, item in enumerate(shopping_cart, start=1):
        ingredients.append(
            f"{index}. {item['ingredient__name'].capitalize()} "
            f"- {item['amount']} "
            f"{item['ingredient__measurement_unit']}"
        )
    for index, item in enumerate(unique_recipes, start=1):
        recipes.append(f"{index}. {item.capitalize()}")
    content = "\n".join(
        [
            f"Дата и время: {current_time}",
            "\nСписок покупок:",
            *ingredients,
            "\nСписок рецептов:",
            *recipes,
        ]
    )
    return FileResponse(
        content, as_attachment=True, filename="shopping_list.txt"
    )
