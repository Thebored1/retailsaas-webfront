from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import ShopConfig
from catalog.models import Product, Inventory
from orders.models import OnlineOrder

RAW_KEY = "test-key-for-tests"


class SyncApiTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        # Create ShopConfig with known key
        ShopConfig.objects.update_or_create(
            pk=1,
            defaults={"api_key": RAW_KEY, "shop_name": "Test Shop"},
        )

    def _auth_headers(self):
        return {"HTTP_X_API_KEY": RAW_KEY}

    def test_requires_api_key(self):
        url = "/api/v1/sync/products"
        response = self.api.post(url, {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_sync_products_full(self):
        url = "/api/v1/sync/products"
        payload = {
            "mode": "full",
            "sent_at": timezone.now().isoformat(),
            "products": [
                {
                    "external_id": "p1",
                    "name": "Prod 1",
                    "sku": "SKU1",
                    "price_estimate": "10.00",
                    "hsn_code": "1001",
                    "gst_rate": "5.00",
                    "is_active": True,
                    "updated_at": timezone.now().isoformat(),
                }
            ],
        }
        response = self.api.post(url, payload, format="json", **self._auth_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)

        # Full sync should deactivate missing items
        payload["products"] = []
        response = self.api.post(url, payload, format="json", **self._auth_headers())
        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(external_id="p1")
        self.assertFalse(product.is_active)

    def test_sync_inventory_full_sets_missing_to_zero(self):
        product = Product.objects.create(
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
            product=product,
            qty_available=5,
            updated_at=timezone.now(),
        )

        url = "/api/v1/sync/inventory"
        payload = {
            "mode": "full",
            "sent_at": timezone.now().isoformat(),
            "inventory": [],
        }
        response = self.api.post(url, payload, format="json", **self._auth_headers())
        self.assertEqual(response.status_code, 200)
        inv = Inventory.objects.get(product=product)
        self.assertEqual(inv.qty_available, 0)

    def test_pending_orders_and_decision(self):
        product = Product.objects.create(
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
            product=product,
            qty_available=5,
            updated_at=timezone.now(),
        )
        order = OnlineOrder.objects.create(
            status=OnlineOrder.Status.PENDING,
            items_json={"items": [{"product_external_id": "p1", "qty": 1}]},
            estimated_total=10,
        )

        pending = self.api.get("/api/v1/orders/pending", format="json", **self._auth_headers())
        self.assertEqual(pending.status_code, 200)
        self.assertEqual(len(pending.data["orders"]), 1)

        decision_payload = {
            "order_id": order.id,
            "decision": "ACCEPT",
            "final_total": "12.50",
        }
        decision = self.api.post(
            "/api/v1/orders/decision",
            decision_payload,
            format="json",
            **self._auth_headers(),
        )
        self.assertEqual(decision.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, OnlineOrder.Status.ACCEPTED)
        self.assertEqual(str(order.final_total), "12.50")
