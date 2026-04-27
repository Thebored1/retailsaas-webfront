from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "phone", "name", "email", "address", "created_at", "updated_at")
    search_fields = ("phone", "name", "email")
    list_filter = ("created_at",)
