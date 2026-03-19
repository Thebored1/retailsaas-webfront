import uuid
from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer


class OnlineOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        ACCEPTED = "ACCEPTED"
        OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
        DELIVERED = "DELIVERED"
        REJECTED = "REJECTED"

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    items_json = models.JSONField()
    estimated_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pricing_breakdown_json = models.JSONField(null=True, blank=True)
    expected_delivery_text = models.CharField(max_length=255, blank=True, default="")
    expected_delivery_start = models.CharField(max_length=10, blank=True, default="")
    expected_delivery_end = models.CharField(max_length=10, blank=True, default="")
    delivery_slot_label = models.CharField(max_length=120, blank=True, default="")
    delivery_slot_start = models.CharField(max_length=10, blank=True, default="")
    delivery_slot_end = models.CharField(max_length=10, blank=True, default="")
    delivery_slot_text = models.CharField(max_length=255, blank=True, default="")
    delivery_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    synced_to_desktop_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delivered_orders",
    )

    def __str__(self) -> str:
        return f"Order {self.id} ({self.status})"

class RetailTransaction(models.Model):
    # Matches the Drift SalesBills table schema in Flutter
    desktop_id = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='retail_transactions')
    date = models.DateTimeField()
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(max_length=20)
    items_json = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Retail TX {self.desktop_id} - {self.grand_total}"


class DeliveryProof(models.Model):
    order = models.ForeignKey(
        OnlineOrder,
        on_delete=models.CASCADE,
        related_name="delivery_proofs",
    )
    image = models.ImageField(upload_to="delivery_proofs/")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delivery_photos",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"DeliveryProof {self.id} for Order {self.order_id}"
