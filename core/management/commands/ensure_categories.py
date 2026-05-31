from django.core.management.base import BaseCommand
from core.models import Category


class Command(BaseCommand):
    help = 'Crée les catégories Plat et Boisson si elles sont absentes.'

    def handle(self, *args, **options):
        for nom in ('Plat', 'Boisson'):
            obj, created = Category.objects.get_or_create(nom=nom)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Catégorie créée : {nom} (id={obj.id})'))
            else:
                self.stdout.write(f'Catégorie déjà présente : {nom} (id={obj.id})')
