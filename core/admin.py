from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, Category, Product, Order, Expense, Task, StockEntry


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('ChezWizi', {'fields': ('telephone',)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('ChezWizi', {'fields': ('telephone',)}),
    )
    list_display = ('username', 'email', 'telephone', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'telephone')


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Expense)
admin.site.register(Task)
admin.site.register(StockEntry)
