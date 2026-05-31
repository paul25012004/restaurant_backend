from django.db import migrations


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    defaults = [
        ('Plat', 'plat'),
        ('Boisson', 'boisson'),
    ]
    for nom, slug in defaults:
        Category.objects.get_or_create(nom=nom, defaults={'slug': slug})


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    Category.objects.filter(nom__in=['Plat', 'Boisson']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_orderitem_product_alter_product_categorie'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, remove_default_categories),
    ]
