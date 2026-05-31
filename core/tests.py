import base64
import os
import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Category, Product, Order, OrderItem, StockEntry

class DeletionSafetyTests(APITestCase):

    def setUp(self):
        # Use a temporary media root for image upload tests.
        self.media_root = tempfile.mkdtemp()
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        # Create user and authenticate
        self.user = User.objects.create_superuser(username='admin', password='adminpassword', email='admin@test.com')
        self.client.force_authenticate(user=self.user)

        # Create Categories
        self.category_plats = Category.objects.create(nom='Plats')
        self.category_boissons = Category.objects.create(nom='Boissons')
        self.category_empty = Category.objects.create(nom='EmptyCat')

        # Create a Product
        self.product = Product.objects.create(
            nom='Bissap',
            categorie=self.category_boissons,
            prix=500,
            stock=10,
            is_active=True
        )

        # Create Orders
        self.order_recu = Order.objects.create(statut='recu', montant_total=500)
        self.order_livre = Order.objects.create(statut='livre', montant_total=1000)

        self.order_item = OrderItem.objects.create(
            order=self.order_recu,
            product=self.product,
            quantite=1,
            prix_unitaire=500
        )

        # Create Stock Entry
        self.stock_entry = StockEntry.objects.create(
            product=self.product,
            quantite=5,
            notes='Test Entry'
        )

    def test_delete_category_with_products_blocked(self):
        """Deleting a category that contains products should return 400 Bad Request."""
        url = reverse('category-detail', args=[self.category_boissons.id])
        response = self.client.delete(url)
        self.assertEqual(response.statusCode if hasattr(response, 'statusCode') else response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Impossible de supprimer cette catégorie car elle contient des produits rattachés.", response.data['detail'])

    def test_delete_category_empty_allowed(self):
        """Deleting an empty category should succeed (204 No Content)."""
        url = reverse('category-detail', args=[self.category_plats.id])
        response = self.client.delete(url)
        self.assertEqual(response.statusCode if hasattr(response, 'statusCode') else response.status_code, status.HTTP_204_NO_CONTENT)


    def test_delete_stock_entry_blocked(self):
        """Deleting a StockEntry should always be blocked to preserve history."""
        url = reverse('stockentry-detail', args=[self.stock_entry.id])
        response = self.client.delete(url)
        self.assertEqual(response.statusCode if hasattr(response, 'statusCode') else response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("La suppression des entrées d'approvisionnement est désactivée", response.data['detail'])

    def test_delete_received_order_allowed(self):
        """Deleting an order with 'recu' status should succeed and restore stock."""
        initial_stock = self.product.stock
        url = reverse('order-detail', args=[self.order_recu.id])
        response = self.client.delete(url)
        self.assertEqual(response.statusCode if hasattr(response, 'statusCode') else response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify signal restored product stock
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock + self.order_item.quantite)

    def test_delete_delivered_order_blocked(self):
        """Deleting an order with 'livre' status should return 400 Bad Request."""
        url = reverse('order-detail', args=[self.order_livre.id])
        response = self.client.delete(url)
        self.assertEqual(response.statusCode if hasattr(response, 'statusCode') else response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Impossible de supprimer une commande déjà livrée.", response.data['detail'])
    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)
    def test_product_create_with_image_upload(self):
        """Creating a product with an image should store the file and return an image URL."""
        small_png = base64.b64decode(
            'R0lGODdhAQABAPAAAP///wAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=='
        )
        uploaded = SimpleUploadedFile('drink.gif', small_png, content_type='image/gif')
        url = reverse('product-list')
        data = {
            'nom': 'Test Bissap',
            'categorie': self.category_boissons.id,
            'prix': '1200.00',
            'description': 'Test upload image',
            'stock': '10',
            'is_active': 'true',
            'image': uploaded,
        }
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.statusCode if hasattr(response, 'statusCode') else response.status_code, status.HTTP_201_CREATED)
        self.assertIn('image_url', response.data)
        self.assertTrue(response.data['image_url'])

        product = Product.objects.get(id=response.data['id'])
        self.assertIsNotNone(product.image)
        self.assertTrue(product.image.name.endswith('drink.gif'))
        self.assertTrue(os.path.exists(product.image.path))

    def test_product_update_with_image_upload(self):
        """Updating a product with a new image should replace the stored file."""
        product = Product.objects.create(
            nom='Old Soda',
            categorie=self.category_boissons,
            prix=800,
            stock=5,
            is_active=True,
        )
        small_png = base64.b64decode(
            'R0lGODdhAQABAPAAAP///wAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=='
        )
        uploaded = SimpleUploadedFile('new-drink.gif', small_png, content_type='image/gif')
        url = reverse('product-detail', args=[product.id])
        data = {
            'nom': 'Old Soda',
            'categorie': self.category_boissons.id,
            'prix': '800.00',
            'description': 'Updated image',
            'stock': '5',
            'is_active': 'true',
            'image': uploaded,
        }
        response = self.client.patch(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image_url', response.data)
        self.assertTrue(response.data['image_url'])

        product.refresh_from_db()
        self.assertIsNotNone(product.image)
        self.assertTrue(product.image.name.endswith('new-drink.gif'))
        self.assertTrue(os.path.exists(product.image.path))
