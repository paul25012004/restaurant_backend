import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_backend.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from core.models import User, Category, Product, Order, OrderItem, Expense, Task


def seed():
    print("Nettoyage...")
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Expense.objects.all().delete()
    Task.objects.all().delete()
    User.objects.all().delete()

    admin = User.objects.create_user(
        username='admin', email='admin@chezwizi.com', password='admin123',
        first_name='Admin', last_name='ChezWizi', is_staff=True, is_superuser=True
    )
    print("Admin cree : admin / admin123")

    plat_cat = Category.objects.create(nom="Plat")
    boisson_cat = Category.objects.create(nom="Boisson")
    print("2 categories creees : Plat, Boisson")

    p1 = Product.objects.create(
        nom="Pizza Margherita", categorie=plat_cat, prix=6500,
        description="Tomate, mozzarella, basilic frais.", stock=30, seuil_alerte=5,
    )
    p2 = Product.objects.create(
        nom="Burger Double", categorie=plat_cat, prix=7000,
        description="Double steak, cheddar, oignons caramelises.", stock=25, seuil_alerte=5,
    )
    p3 = Product.objects.create(
        nom="Poulet Braise", categorie=plat_cat, prix=5500,
        description="Poulet grille avec frites et salade.", stock=35, seuil_alerte=6,
    )
    p4 = Product.objects.create(
        nom="Coca-Cola", categorie=boisson_cat, prix=1500,
        description="Canette 33cl.", stock=50, seuil_alerte=10,
    )
    p5 = Product.objects.create(
        nom="Jus Gingembre", categorie=boisson_cat, prix=2000,
        description="Jus de gingembre frais maison.", stock=40, seuil_alerte=8,
    )
    p6 = Product.objects.create(
        nom="Eau Minerale", categorie=boisson_cat, prix=1000,
        description="Bouteille 50cl.", stock=60, seuil_alerte=12,
    )
    print("6 produits crees")

    today = timezone.localdate()
    for i in range(5):
        o = Order.objects.create(statut='livre' if i > 0 else 'recu', notes='')
        o.date_creation = timezone.now() - timedelta(days=i, hours=2)
        o.save()
        OrderItem.objects.create(order=o, product=p1, quantite=2, prix_unitaire=p1.prix)
        OrderItem.objects.create(order=o, product=p4, quantite=3, prix_unitaire=p4.prix)
        o.montant_total = (p1.prix * 2) + (p4.prix * 3)
        o.save()

    o2 = Order.objects.create(statut='recu', notes='Sans oignons')
    OrderItem.objects.create(order=o2, product=p2, quantite=1, prix_unitaire=p2.prix)
    OrderItem.objects.create(order=o2, product=p5, quantite=2, prix_unitaire=p5.prix)
    o2.montant_total = p2.prix + (p5.prix * 2)
    o2.save()
    print("6 commandes creees")

    Expense.objects.create(montant=45000, categorie='ingredients', description='Legumes et poulet au marche.')
    Expense.objects.create(montant=15000, categorie='internet', description='Abonnement fibre mensuel.')
    e3 = Expense.objects.create(montant=35000, categorie='ingredients', description='Boissons chez le grossiste.')
    e3.date = today - timedelta(days=1)
    e3.save()
    Expense.objects.create(montant=8000, categorie='transport', description='Livraison fournisseur.')
    print("4 depenses creees")

    Task.objects.create(titre="Acheter glacons", description="3 sacs au supermarche.", statut='a_faire')
    Task.objects.create(titre="Reparer ventilateur salle", description="Appeler electricien.", statut='a_faire')
    Task.objects.create(titre="Mettre a jour menu ardoise", description="", statut='fait')
    print("3 taches creees")

    print("=== Seed termine ! ===")


if __name__ == '__main__':
    seed()
