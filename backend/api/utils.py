from django.http import FileResponse
from django.utils import timezone


TIME_FORMAT = "%d-%m-%Y %H:%M"


def make_shopping_cart_file(shopping_cart):
    current_time = timezone.now().strftime(TIME_FORMAT)
    ingredients = []
    recipes = []
    recipes_names = []
    for index, item in enumerate(shopping_cart, start=1):
        ingredients.append(
            f"{index}. "
            f"{item['ingredient__name']} - {item['amount']}"
            f" {item['ingredient__measurement_unit']}"
        )
        recipes.append(item["recipe__name"])
    print(f"{recipes_names = }")
    for index, item in enumerate(set(recipes), start=1):
        recipes_names.append(f"{index}. {item}")
    content = "\n".join(
        [
            f"Дата и время: {current_time}",
            "\nСписок покупок:",
            *ingredients,
            "\nСписок рецептов:",
            *recipes_names,
        ]
    )
    return FileResponse(
        content, as_attachment=True, filename="shopping_list.txt"
    )
