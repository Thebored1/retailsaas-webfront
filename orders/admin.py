from django.contrib import admin
from .models import OnlineOrder, DeliveryProof


@admin.register(OnlineOrder)
class OnlineOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "estimated_total",
        "final_total",
        "created_at",
        "delivered_at",
    )
    list_filter = ("status",)
    search_fields = ("id",)


@admin.register(DeliveryProof)
class DeliveryProofAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "uploaded_by", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("order__id",)
