from django.contrib import admin
from .models import Product, Inventory, Category, ProductBatch


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "external_id")
    search_fields = ("name", "external_id")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "sku", "mrp", "price_estimate", "uom", "is_active", "updated_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "external_id", "sku")


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product", "qty_available", "updated_at")
    list_filter = ()


@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ("product", "batch_number", "selling_price", "qty_available", "created_at")
    list_filter = ("product",)
    search_fields = ("product__name", "batch_number", "external_id")
