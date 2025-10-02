import csv

from django.core.management.base import BaseCommand

from recipes.models import Tag

PATH_TO_CSV = 'data/tags.csv'


def load_file(filename):
    with open(filename, mode='r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        data = [Tag(name=item[0], slug=item[1])
                for item in reader]
    return data


class Command(BaseCommand):
    help = 'Load tags.csv to BD'

    def handle(self, *args, **options):
        content = load_file(PATH_TO_CSV)
        Tag.objects.bulk_create(content, ignore_conflicts=True)
        self.stdout.write(
            self.style.SUCCESS(f'{len(content)} records were processed.')
        )
