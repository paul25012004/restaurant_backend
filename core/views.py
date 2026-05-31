from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta

from .models import User, Category, Product, Order, OrderItem, Expense, Task, StockEntry
from .serializers import (
    UserSerializer, CategorySerializer, ProductSerializer,
    OrderSerializer, ExpenseSerializer, TaskSerializer, StockEntrySerializer
)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        return Response({"detail": "Identifiants invalides."}, status=status.HTTP_401_UNAUTHORIZED)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(nom__in=['Plat', 'Boisson', 'Plats', 'Boissons']).order_by('nom')
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.products.exists():
            return Response(
                {"detail": "Impossible de supprimer cette catégorie car elle contient des produits rattachés."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('nom')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        qs = Product.objects.all().order_by('nom')
        
        # Only filter by is_active=True for list/GET requests unless specified otherwise
        if self.action == 'list':
            qs = qs.filter(is_active=True)
            
        cat = self.request.query_params.get('categorie')
        if cat:
            qs = qs.filter(categorie_id=cat)
        product_type = self.request.query_params.get('type')
        if product_type == 'boisson':
            qs = qs.filter(categorie__nom__icontains='boisson')
        elif product_type == 'plat':
            qs = qs.filter(categorie__nom__icontains='plat')
        return qs

    def _ensure_media_dir(self):
        """Ensure the media/products/ directory exists."""
        import os
        from django.conf import settings
        media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        os.makedirs(media_dir, exist_ok=True)

    def perform_create(self, serializer):
        import logging
        logger = logging.getLogger(__name__)
        self._ensure_media_dir()
        logger.info(f"[PRODUCT CREATE] FILES={list(self.request.FILES.keys())}, DATA keys={list(self.request.data.keys())}")
        image = self.request.FILES.get('image')
        if image is not None:
            logger.info(f"[PRODUCT CREATE] Image received: {image.name}, size={image.size}")
            serializer.save(image=image)
        else:
            serializer.save()

    def perform_update(self, serializer):
        import logging
        logger = logging.getLogger(__name__)
        self._ensure_media_dir()
        logger.info(f"[PRODUCT UPDATE] FILES={list(self.request.FILES.keys())}, DATA keys={list(self.request.data.keys())}")
        image = self.request.FILES.get('image')
        if image is not None:
            logger.info(f"[PRODUCT UPDATE] Image received: {image.name}, size={image.size}")
            serializer.save(image=image)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.statut == 'livre':
            return Response(
                {"detail": "Impossible de supprimer une commande déjà livrée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


    def get_queryset(self):
        qs = Order.objects.all()
        s = self.request.query_params.get('statut')
        if s:
            qs = qs.filter(statut=s)
        today = self.request.query_params.get('today')
        if today == 'true':
            qs = qs.filter(date_creation__date=timezone.localdate())
        return qs


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Les dépenses enregistrées ne peuvent pas être modifiées afin de préserver l'historique comptable."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Les dépenses enregistrées ne peuvent pas être supprimées afin de préserver les statistiques comptables."},
            status=status.HTTP_400_BAD_REQUEST
        )


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]


class StockEntryViewSet(viewsets.ModelViewSet):
    queryset = StockEntry.objects.all().order_by('-date')
    serializer_class = StockEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "La suppression des entrées d'approvisionnement est désactivée pour préserver l'historique de stock."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Les entrées d'approvisionnement ne peuvent pas être modifiées afin de garantir la cohérence des stocks."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)



class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        import calendar

        # Get query parameters
        date_param = request.query_params.get('date')
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year')

        # Determine filtering type and range
        is_filtered = False
        filter_label = ""
        
        # Base querysets
        orders = Order.objects.all()
        expenses = Expense.objects.all()
        order_items = OrderItem.objects.all()

        today = timezone.localdate()

        if date_param:
            try:
                # Filter by a specific day YYYY-MM-DD
                target_date = timezone.datetime.strptime(date_param, '%Y-%m-%d').date()
                orders = orders.filter(date_creation__date=target_date)
                expenses = expenses.filter(date=target_date)
                order_items = order_items.filter(order__date_creation__date=target_date)
                filter_label = target_date.strftime('%d/%m/%Y')
                is_filtered = True
            except ValueError:
                pass
        elif month_param and year_param:
            try:
                # Filter by a specific month + year
                m = int(month_param)
                y = int(year_param)
                orders = orders.filter(date_creation__year=y, date_creation__month=m)
                expenses = expenses.filter(date__year=y, date__month=m)
                order_items = order_items.filter(order__date_creation__year=y, order__date_creation__month=m)
                
                months_fr = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
                filter_label = f"{months_fr[m]} {y}"
                is_filtered = True
            except (ValueError, IndexError):
                pass
        elif year_param:
            try:
                # Filter by a specific year YYYY
                y = int(year_param)
                orders = orders.filter(date_creation__year=y)
                expenses = expenses.filter(date__year=y)
                order_items = order_items.filter(order__date_creation__year=y)
                filter_label = f"Année {y}"
                is_filtered = True
            except ValueError:
                pass

        if is_filtered:
            # Stats for the filtered period
            total_commandes = orders.count()
            commandes_recues = orders.filter(statut='recu').count()
            commandes_livrees = orders.filter(statut='livre').count()

            ca = orders.aggregate(t=Sum('montant_total'))['t'] or 0
            dep = expenses.aggregate(t=Sum('montant'))['t'] or 0
            benefice = float(ca) - float(dep)

            # Map to response keys to support existing widgets on dashboard
            total_commandes_jour = total_commandes
            total_commandes_mois = total_commandes
            ca_jour = ca
            ca_mois = ca
            dep_jour = dep
            dep_mois = dep
            benefice_jour = benefice
            benefice_mois = benefice

            # Top 5 plats vendus during this filtered period
            top_plats = (
                order_items
                .values('product__nom')
                .annotate(total_qty=Sum('quantite'))
                .order_by('-total_qty')[:5]
            )

            # Répartition dépenses par catégorie during this filtered period
            dep_categories = (
                expenses
                .values('categorie')
                .annotate(total=Sum('montant'))
                .order_by('-total')
            )

            # Évolution chart
            evolution = []
            if date_param:
                # Show 7 days ending at selected date
                for i in range(6, -1, -1):
                    d = target_date - timedelta(days=i)
                    v = Order.objects.filter(date_creation__date=d).aggregate(t=Sum('montant_total'))['t'] or 0
                    dp = Expense.objects.filter(date=d).aggregate(t=Sum('montant'))['t'] or 0
                    evolution.append({
                        'date': d.strftime('%d/%m'),
                        'ventes': float(v),
                        'depenses': float(dp),
                    })
            elif month_param and year_param:
                # Show month grouped by weeks/blocks
                _, num_days = calendar.monthrange(y, m)
                ranges = [
                    ("01-07", 1, 7),
                    ("08-14", 8, 14),
                    ("15-21", 15, 21),
                    ("22-28", 22, 28),
                ]
                if num_days > 28:
                    ranges.append((f"29-{num_days}", 29, num_days))
                    
                for label, start_day, end_day in ranges:
                    v = Order.objects.filter(
                        date_creation__year=y, 
                        date_creation__month=m,
                        date_creation__date__day__gte=start_day,
                        date_creation__date__day__lte=end_day
                    ).aggregate(t=Sum('montant_total'))['t'] or 0
                    dp = Expense.objects.filter(
                        date__year=y,
                        date__month=m,
                        date__day__gte=start_day,
                        date__day__lte=end_day
                    ).aggregate(t=Sum('montant'))['t'] or 0
                    evolution.append({
                        'date': label,
                        'ventes': float(v),
                        'depenses': float(dp),
                    })
            elif year_param:
                # Show month-by-month
                months_short = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Jui", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
                for mi in range(1, 13):
                    v = Order.objects.filter(date_creation__year=y, date_creation__month=mi).aggregate(t=Sum('montant_total'))['t'] or 0
                    dp = Expense.objects.filter(date__year=y, date__month=mi).aggregate(t=Sum('montant'))['t'] or 0
                    evolution.append({
                        'date': months_short[mi],
                        'ventes': float(v),
                        'depenses': float(dp),
                    })
        else:
            # Default behavior (no active filter)
            month_start = today.replace(day=1)

            orders_today = Order.objects.filter(date_creation__date=today)
            orders_month = Order.objects.filter(date_creation__date__gte=month_start)

            total_commandes_jour = orders_today.count()
            total_commandes_mois = orders_month.count()
            commandes_recues = orders_today.filter(statut='recu').count()
            commandes_livrees = orders_today.filter(statut='livre').count()

            ca_jour = orders_today.aggregate(t=Sum('montant_total'))['t'] or 0
            ca_mois = orders_month.aggregate(t=Sum('montant_total'))['t'] or 0

            dep_jour = Expense.objects.filter(date=today).aggregate(t=Sum('montant'))['t'] or 0
            dep_mois = Expense.objects.filter(date__gte=month_start).aggregate(t=Sum('montant'))['t'] or 0

            benefice_jour = float(ca_jour) - float(dep_jour)
            benefice_mois = float(ca_mois) - float(dep_mois)

            top_plats = (
                OrderItem.objects
                .filter(order__date_creation__date__gte=month_start)
                .values('product__nom')
                .annotate(total_qty=Sum('quantite'))
                .order_by('-total_qty')[:5]
            )

            dep_categories = (
                Expense.objects
                .filter(date__gte=month_start)
                .values('categorie')
                .annotate(total=Sum('montant'))
                .order_by('-total')
            )

            evolution = []
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                v = Order.objects.filter(date_creation__date=d).aggregate(t=Sum('montant_total'))['t'] or 0
                dp = Expense.objects.filter(date=d).aggregate(t=Sum('montant'))['t'] or 0
                evolution.append({
                    'date': d.strftime('%d/%m'),
                    'ventes': float(v),
                    'depenses': float(dp),
                })

        cat_map = dict(Expense.CATEGORY_CHOICES)

        taches_a_faire = Task.objects.filter(statut='a_faire').count()
        taches_faites = Task.objects.filter(statut='fait').count()

        return Response({
            'is_filtered': is_filtered,
            'filter_label': filter_label,
            'total_commandes_jour': total_commandes_jour,
            'total_commandes_mois': total_commandes_mois,
            'commandes_recues': commandes_recues,
            'commandes_livrees': commandes_livrees,
            'ca_jour': float(ca_jour),
            'ca_mois': float(ca_mois),
            'depenses_jour': float(dep_jour),
            'depenses_mois': float(dep_mois),
            'benefice_jour': benefice_jour,
            'benefice_mois': benefice_mois,
            'top_plats': [
                {'nom': p['product__nom'] if p.get('product__nom') else (p['nom'] if p.get('nom') else 'Inconnu'), 'quantite': p['total_qty']}
                for p in top_plats
            ],
            'depenses_par_categorie': [
                {'categorie': cat_map.get(d['categorie'], d['categorie']),
                 'total': float(d['total'])}
                for d in dep_categories
            ],
            'evolution': evolution,
            'taches_a_faire': taches_a_faire,
            'taches_faites': taches_faites,
        })

