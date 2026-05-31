from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class User(AbstractUser):
    """Utilisateur unique admin du restaurant."""
    telephone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username


class Category(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Product(models.Model):
    nom = models.CharField(max_length=200)
    categorie = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.IntegerField(default=0)
    seuil_alerte = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} — {self.prix} FCFA"


class Order(models.Model):
    STATUS_CHOICES = [
        ('recu', 'Reçu'),
        ('livre', 'Livré / Servi'),
    ]
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='recu')
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default='')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Commande #{self.id} — {self.get_statut_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantite}x {self.product.nom}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('ingredients', 'Ingrédients'),
        ('electricite', 'Électricité'),
        ('eau', 'Eau'),
        ('internet', 'Internet'),
        ('salaire', 'Salaire'),
        ('maintenance', 'Maintenance'),
        ('transport', 'Transport'),
        ('publicite', 'Publicité'),
        ('autre', 'Autre'),
    ]
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    categorie = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='autre')
    description = models.TextField()
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_categorie_display()} — {self.montant} FCFA"


class Task(models.Model):
    STATUS_CHOICES = [
        ('a_faire', 'À faire'),
        ('fait', 'Fait'),
    ]
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='a_faire')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} ({self.get_statut_display()})"


class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    quantite = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"+{self.quantite} {self.product.nom} le {self.date}"


from django.db.models.signals import pre_delete
from django.dispatch import receiver

@receiver(pre_delete, sender=Order)
def restore_stock_on_order_delete(sender, instance, **kwargs):
    for item in instance.items.all():
        prod = item.product
        prod.stock += item.quantite
        prod.save()
