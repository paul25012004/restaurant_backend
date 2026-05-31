from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, CategoryViewSet, ProductViewSet,
    OrderViewSet, ExpenseViewSet, TaskViewSet, DashboardView, StockEntryViewSet
)

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('products', ProductViewSet)
router.register('orders', OrderViewSet)
router.register('expenses', ExpenseViewSet)
router.register('tasks', TaskViewSet)
router.register('stock-entries', StockEntryViewSet)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', include(router.urls)),
]
