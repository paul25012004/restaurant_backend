from rest_framework import serializers
from .models import User, Category, Product, Order, OrderItem, Expense, Task, StockEntry


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'telephone', 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'nom', 'slug']


class ProductSerializer(serializers.ModelSerializer):
    categorie_name = serializers.ReadOnlyField(source='categorie.nom')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'nom', 'categorie', 'categorie_name', 'prix',
            'description', 'image', 'image_url', 'stock', 'seuil_alerte',
            'is_active', 'date_creation',
        ]
        extra_kwargs = {'image': {'required': False, 'allow_null': True}}

    def get_image_url(self, obj):
        if not obj.image:
            return None
        url = obj.image.url
        if url.startswith('http://') or url.startswith('https://'):
            return url
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.nom')

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantite', 'prix_unitaire']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    statut_display = serializers.ReadOnlyField(source='get_statut_display')

    class Meta:
        model = Order
        fields = ['id', 'statut', 'statut_display', 'montant_total',
                  'notes', 'date_creation', 'date_modification', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        total = 0
        for item in items_data:
            OrderItem.objects.create(order=order, **item)
            total += item['prix_unitaire'] * item['quantite']
            # Decrement stock!
            product = item['product']
            product.stock = max(0, product.stock - item['quantite'])
            product.save()
        order.montant_total = total
        order.save()
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        instance = super().update(instance, validated_data)
        if items_data is not None:
            # Restore stock of old items before deleting them
            for old_item in instance.items.all():
                prod = old_item.product
                prod.stock += old_item.quantite
                prod.save()

            instance.items.all().delete()
            total = 0
            for item in items_data:
                OrderItem.objects.create(order=instance, **item)
                total += item['prix_unitaire'] * item['quantite']
                # Decrement stock
                prod = item['product']
                prod.stock = max(0, prod.stock - item['quantite'])
                prod.save()
            instance.montant_total = total
            instance.save()
        return instance


class ExpenseSerializer(serializers.ModelSerializer):
    categorie_display = serializers.ReadOnlyField(source='get_categorie_display')

    class Meta:
        model = Expense
        fields = ['id', 'montant', 'categorie', 'categorie_display',
                  'description', 'date']


class TaskSerializer(serializers.ModelSerializer):
    statut_display = serializers.ReadOnlyField(source='get_statut_display')

    class Meta:
        model = Task
        fields = ['id', 'titre', 'description', 'statut', 'statut_display',
                  'date_creation']


class StockEntrySerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.nom')

    class Meta:
        model = StockEntry
        fields = ['id', 'product', 'product_name', 'quantite', 'date', 'notes']

    def create(self, validated_data):
        entry = super().create(validated_data)
        # Increment stock of the product!
        prod = entry.product
        prod.stock += entry.quantite
        prod.save()
        return entry
