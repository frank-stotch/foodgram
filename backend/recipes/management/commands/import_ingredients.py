import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

PATH_CSV = "data/ingredients.csv"


class Command(BaseCommand):
    help = "Import data from CSV file into the database"

    def handle(self, *args, **kwargs):
        with open(PATH_CSV, "r", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)
            Ingredient.objects.bulk_create(
                (Ingredient(**row) for row in csv_reader),
                ignore_conflicts=True,
            )
        self.stdout.write(self.style.SUCCESS("Data imported successfully"))
