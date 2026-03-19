from rest_framework import serializers


class ProductSyncSerializer(serializers.Serializer):
    external_id = serializers.CharField()
    name = serializers.CharField()
    sku = serializers.CharField(required=False, allow_blank=True)
    price_estimate = serializers.DecimalField(max_digits=12, decimal_places=2)
    hsn_code = serializers.CharField()
    gst_rate = serializers.DecimalField(max_digits=6, decimal_places=2)
    is_active = serializers.BooleanField(required=False)
    updated_at = serializers.DateTimeField(required=False)


class SyncProductsPayloadSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["full", "delta"])
    sent_at = serializers.DateTimeField(required=False)
    products = ProductSyncSerializer(many=True)


class InventorySyncSerializer(serializers.Serializer):
    product_external_id = serializers.CharField()
    qty_available = serializers.DecimalField(max_digits=12, decimal_places=2)
    updated_at = serializers.DateTimeField(required=False)


class SyncInventoryPayloadSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["full", "delta"])
    sent_at = serializers.DateTimeField(required=False)
    inventory = InventorySyncSerializer(many=True)

class CustomerSyncSerializer(serializers.Serializer):
    phone = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField()

class SyncCustomersPayloadSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["full", "delta"])
    sent_at = serializers.DateTimeField(required=False)
    customers = CustomerSyncSerializer(many=True)


class OrderDecisionSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    decision = serializers.ChoiceField(choices=["ACCEPT", "REJECT"])
    final_total = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    pricing_breakdown = serializers.JSONField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    delivery_slot_label = serializers.CharField(required=False, allow_blank=True)
    delivery_slot_start = serializers.CharField(required=False, allow_blank=True)
    delivery_slot_end = serializers.CharField(required=False, allow_blank=True)
    delivery_slot_text = serializers.CharField(required=False, allow_blank=True)
    out_for_delivery = serializers.BooleanField(required=False)
    delivery_date = serializers.DateField(required=False)

class OrderStatusUpdateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["OUT_FOR_DELIVERY"])

class RetailTransactionSyncSerializer(serializers.Serializer):
    desktop_id = serializers.CharField()
    customer_phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    date = serializers.DateTimeField()
    grand_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_status = serializers.CharField()
    items_json = serializers.JSONField(default=list)

class SyncSalesPayloadSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["full", "delta"])
    sent_at = serializers.DateTimeField(required=False)
    sales = RetailTransactionSyncSerializer(many=True)


class SyncResetPayloadSerializer(serializers.Serializer):
    sent_at = serializers.DateTimeField(required=False)
    products = ProductSyncSerializer(many=True)
    inventory = InventorySyncSerializer(many=True)


class DeliverySettingsSerializer(serializers.Serializer):
    require_delivery_photo = serializers.BooleanField()


class BatchSyncSerializer(serializers.Serializer):
    id = serializers.CharField()
    product_external_id = serializers.CharField()
    batch_number = serializers.CharField(required=False, allow_blank=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    selling_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    qty_available = serializers.DecimalField(max_digits=12, decimal_places=2)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class SyncBatchesPayloadSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["full", "delta"])
    sent_at = serializers.DateTimeField(required=False)
    batches = BatchSyncSerializer(many=True)


class DeliveryAgentCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    full_name = serializers.CharField()


class DeliveryAgentUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class DeliveryAgentDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    username = serializers.CharField(required=False)
