from django.test import TestCase
from django.utils import timezone
from catalog.models import Product, Inventory, ProductBatch
from orders.models import OnlineOrder


class CheckoutFlowTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            external_id="p1",
            name="Prod 1",
            sku="",
            price_estimate=10,
            hsn_code="1001",
            gst_rate=5,
            is_active=True,
            updated_at=timezone.now(),
        )
        Inventory.objects.create(
            product=self.product,
            qty_available=10,
            updated_at=timezone.now(),
        )
        ProductBatch.objects.create(
            product=self.product,
            external_id="b1",
            batch_number="B1",
            selling_price=10,
            qty_available=10,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

    def test_checkout_creates_order(self):
        self.client.post(f"/cart/add/{self.product.id}/", {"qty": 2})
        response = self.client.post(
            "/checkout/",
            {
                "customer_name": "John",
                "customer_phone": "1234567890",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OnlineOrder.objects.count(), 1)
        order = OnlineOrder.objects.first()
        self.assertEqual(order.status, OnlineOrder.Status.PENDING)
