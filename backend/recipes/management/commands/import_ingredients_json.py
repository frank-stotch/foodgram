import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

PATH_JSON = 'data/ingredients.json'


class Command(BaseCommand):
    help = 'Import data from JSON file into the database'

    def handle(self, *args, **kwargs):
        objects_to_create = []
        with open(PATH_JSON, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                objects_to_create.append(Ingredient(**item))
        Ingredient.objects.bulk_create(objects_to_create, batch_size=500)
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
