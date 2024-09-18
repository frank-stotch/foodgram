import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

PATH_JSON = "data/ingredients.json"


class Command(BaseCommand):
    help = "Import data from JSON file into the database"

    def handle(self, *args, **kwargs):
        with open(PATH_JSON, "r", encoding="utf-8") as file:
            data = json.load(file)
            Ingredient.objects.bulk_create(
                (Ingredient(**ingredient) for ingredient in data),
                ignore_conflicts=True,
            )
        self.stdout.write(self.style.SUCCESS("Data imported successfully"))
