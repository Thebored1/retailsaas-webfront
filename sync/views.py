from decimal import Decimal
import base64
import urllib.request

from django.conf import settings
from django.db import transaction, models
from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import Group, User

from catalog.models import Product, Inventory, ProductBatch, Category
from orders.models import OnlineOrder, RetailTransaction
from customers.models import Customer
from .auth import APIKeyAuthentication
from customers.models import Customer
from .serializers import (
    SyncProductsPayloadSerializer,
    SyncInventoryPayloadSerializer,
    SyncCustomersPayloadSerializer,
    OrderDecisionSerializer,
    OrderStatusUpdateSerializer,
    SyncSalesPayloadSerializer,
    SyncResetPayloadSerializer,
    DeliverySettingsSerializer,
    DeliveryAgentCreateSerializer,
    DeliveryAgentUpdateSerializer,
    DeliveryAgentDeleteSerializer,
    SyncBatchesPayloadSerializer,
    SyncCategoriesPayloadSerializer,
)
from core.models import ShopConfig


def _guess_image_ext(data: bytes) -> str:
    if data.startswith(b"\xFF\xD8"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return "jpg"


def _decode_image_data(raw: str) -> bytes:
    data = raw.strip()
    if data.startswith("data:") and "base64," in data:
        data = data.split("base64,", 1)[1]
    return base64.b64decode(data)


def _fetch_image_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return resp.read()


class SyncProductsView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncProductsPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        now = timezone.now()
        mode = payload["mode"]
        products_data = payload["products"]

        external_ids = [p["external_id"] for p in products_data]
        existing = Product.objects.filter(external_id__in=external_ids)
        existing_map = {p.external_id: p for p in existing}

        to_create = []
        to_update = []
        image_payloads = {}

        for data in products_data:
            external_id = data["external_id"]
            updated_at = data.get("updated_at") or now
            is_active = data.get("is_active", True)
            if external_id in existing_map:
                product = existing_map[external_id]
                product.name = data["name"]
                product.sku = data.get("sku", "")
                product.price_estimate = data["price_estimate"]
                product.hsn_code = data["hsn_code"]
                product.gst_rate = data["gst_rate"]
                product.is_active = is_active
                product.updated_at = updated_at
                to_update.append(product)
            else:
                to_create.append(
                    Product(
                        external_id=external_id,
                        name=data["name"],
                        sku=data.get("sku", ""),
                        price_estimate=data["price_estimate"],
                        hsn_code=data["hsn_code"],
                        gst_rate=data["gst_rate"],
                        is_active=is_active,
                        updated_at=updated_at,
                    )
                )

            if data.get("image_clear") or data.get("image_data") or data.get("image_url"):
                image_payloads[external_id] = data

        with transaction.atomic():
            if to_create:
                Product.objects.bulk_create(to_create)
            if to_update:
                Product.objects.bulk_update(
                    to_update,
                    ["name", "sku", "price_estimate", "hsn_code", "gst_rate", "is_active", "updated_at"],
                )
            if mode == "full":
                Product.objects.exclude(external_id__in=external_ids).update(is_active=False)

        image_updated = 0
        image_cleared = 0
        image_failed = []

        if image_payloads:
            products = Product.objects.filter(external_id__in=image_payloads.keys())
            product_map = {p.external_id: p for p in products}

            for external_id, data in image_payloads.items():
                product = product_map.get(external_id)
                if not product:
                    continue

                try:
                    if data.get("image_clear"):
                        if product.image:
                            product.image.delete(save=False)
                        product.image = None
                        product.image_b64 = ""
                        product.save(update_fields=["image", "image_b64"])
                        image_cleared += 1
                        continue

                    img_bytes = None
                    if data.get("image_data"):
                        img_bytes = _decode_image_data(data["image_data"])
                    else:
                        image_url = (data.get("image_url") or "").strip()
                        if image_url.startswith("http://") or image_url.startswith("https://"):
                            img_bytes = _fetch_image_bytes(image_url)

                    if img_bytes:
                        if product.image:
                            product.image.delete(save=False)
                        ext = _guess_image_ext(img_bytes)
                        filename = f"{product.external_id}.{ext}"
                        product.image.save(filename, ContentFile(img_bytes), save=False)
                        # Also store as base64 in DB for backup-friendly storage
                        product.image_b64 = base64.b64encode(img_bytes).decode("utf-8")
                        product.save(update_fields=["image", "image_b64"])
                        image_updated += 1
                except Exception as e:
                    image_failed.append({"external_id": external_id, "error": str(e)})

        return Response(
            {
                "created": len(to_create),
                "updated": len(to_update),
                "mode": mode,
                "image_updated": image_updated,
                "image_cleared": image_cleared,
                "image_failed": image_failed,
            }
        )


class SyncInventoryView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncInventoryPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        now = timezone.now()
        mode = payload["mode"]
        inventory_data = payload["inventory"]

        external_ids = [i["product_external_id"] for i in inventory_data]
        products = Product.objects.filter(external_id__in=external_ids)
        product_map = {p.external_id: p for p in products}

        inventory_existing = Inventory.objects.filter(product__in=products)
        inv_map = {inv.product_id: inv for inv in inventory_existing}

        to_create = []
        to_update = []
        skipped = []

        for data in inventory_data:
            external_id = data["product_external_id"]
            product = product_map.get(external_id)
            if product is None:
                skipped.append(external_id)
                continue
            updated_at = data.get("updated_at") or now
            qty = data["qty_available"]
            existing_inv = inv_map.get(product.id)
            if existing_inv:
                existing_inv.qty_available = qty
                existing_inv.updated_at = updated_at
                to_update.append(existing_inv)
            else:
                to_create.append(
                    Inventory(product=product, qty_available=qty, updated_at=updated_at)
                )

        with transaction.atomic():
            if to_create:
                Inventory.objects.bulk_create(to_create)
            if to_update:
                Inventory.objects.bulk_update(to_update, ["qty_available", "updated_at"])
            if mode == "full":
                Inventory.objects.exclude(product__external_id__in=external_ids).update(
                    qty_available=Decimal("0"), updated_at=now
                )

        return Response({"created": len(to_create), "updated": len(to_update), "skipped": skipped, "mode": mode})


class SyncBatchesView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncBatchesPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        now = timezone.now()
        mode = payload["mode"]
        batches_data = payload["batches"]

        external_ids = [b["product_external_id"] for b in batches_data]
        products = Product.objects.filter(external_id__in=external_ids)
        product_map = {p.external_id: p for p in products}

        batch_ids = [b["id"] for b in batches_data]
        existing = ProductBatch.objects.filter(external_id__in=batch_ids)
        existing_map = {b.external_id: b for b in existing}

        to_create = []
        to_update = []
        skipped = []

        for data in batches_data:
            product = product_map.get(data["product_external_id"])
            if product is None:
                skipped.append(data["product_external_id"])
                continue

            external_id = data["id"]
            created_at = data.get("created_at") or now
            updated_at = data.get("updated_at")

            if external_id in existing_map:
                batch = existing_map[external_id]
                batch.product = product
                batch.batch_number = data.get("batch_number") or ""
                batch.expiry_date = data.get("expiry_date")
                batch.selling_price = data["selling_price"]
                batch.qty_available = data["qty_available"]
                batch.created_at = created_at
                batch.updated_at = updated_at
                to_update.append(batch)
            else:
                to_create.append(
                    ProductBatch(
                        product=product,
                        external_id=external_id,
                        batch_number=data.get("batch_number") or "",
                        expiry_date=data.get("expiry_date"),
                        selling_price=data["selling_price"],
                        qty_available=data["qty_available"],
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                )

        with transaction.atomic():
            if to_create:
                ProductBatch.objects.bulk_create(to_create)
            if to_update:
                ProductBatch.objects.bulk_update(
                    to_update,
                    [
                        "product",
                        "batch_number",
                        "expiry_date",
                        "selling_price",
                        "qty_available",
                        "created_at",
                        "updated_at",
                    ],
                )
            if mode == "full":
                ProductBatch.objects.exclude(external_id__in=batch_ids).delete()

            # Update aggregate inventory totals
            for product in products:
                total_qty = (
                    ProductBatch.objects.filter(product=product)
                    .aggregate(total=models.Sum("qty_available"))
                    .get("total")
                    or Decimal("0")
                )
                Inventory.objects.update_or_create(
                    product=product,
                    defaults={"qty_available": total_qty, "updated_at": now},
                )

        return Response(
            {
                "created": len(to_create),
                "updated": len(to_update),
                "skipped": skipped,
                "mode": mode,
            }
        )


class SyncCustomersView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customers = Customer.objects.all().order_by("-updated_at")
        payload = []
        for c in customers:
            payload.append(
                {
                    "phone": c.phone,
                    "name": c.name,
                    "email": c.email or "",
                    "address": c.address,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at,
                }
            )
        return Response({"customers": payload})

    def post(self, request):
        serializer = SyncCustomersPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        customers_data = payload["customers"]
        mode = payload["mode"]

        created = 0
        updated = 0
        seen_phones = []
        for data in customers_data:
            phone = data["phone"]
            seen_phones.append(phone)
            defaults = {
                "name": data["name"],
                "email": data.get("email") or None,
                "address": data["address"],
            }
            obj, was_created = Customer.objects.update_or_create(
                phone=phone, defaults=defaults
            )
            if obj.user:
                user = obj.user
                desired_username = str(phone)
                if user.username != desired_username:
                    user.username = desired_username
                user.first_name = (data["name"] or "").split()[0] if data["name"] else ""
                user.email = (data.get("email") or "")
                user.save()
            if was_created:
                created += 1
            else:
                updated += 1

        deleted = 0
        deleted_users = 0
        if mode == "full":
            to_delete = Customer.objects.exclude(phone__in=seen_phones)
            user_ids = list(
                to_delete.exclude(user__isnull=True).values_list("user_id", flat=True)
            )
            deleted = to_delete.count()
            to_delete.delete()
            if user_ids:
                deleted_users, _ = User.objects.filter(id__in=user_ids).delete()

        return Response(
            {
                "created": created,
                "updated": updated,
                "deleted": deleted,
                "deleted_users": deleted_users,
                "mode": mode,
            }
        )


class PendingOrdersView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = OnlineOrder.objects.filter(status=OnlineOrder.Status.PENDING).order_by("created_at")

        payload = []
        for order in orders:
            items = order.items_json.get("items") if isinstance(order.items_json, dict) else order.items_json
            customer = {}
            if isinstance(order.items_json, dict):
                customer = order.items_json.get("customer") or {}
            payload.append(
                {
                    "order_id": order.id,
                    "items": items,
                    "customer": customer,
                    "estimated_total": str(order.estimated_total),
                    "created_at": order.created_at,
                    "expected_delivery_text": order.expected_delivery_text,
                    "expected_delivery_start": order.expected_delivery_start,
                    "expected_delivery_end": order.expected_delivery_end,
                }
            )

        return Response({"orders": payload})


class OrdersListView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_param = request.query_params.get("status", "")
        if status_param:
            raw = [s.strip().upper() for s in status_param.split(",") if s.strip()]
            allowed = {
                OnlineOrder.Status.PENDING,
                OnlineOrder.Status.ACCEPTED,
                OnlineOrder.Status.OUT_FOR_DELIVERY,
                OnlineOrder.Status.DELIVERED,
                OnlineOrder.Status.REJECTED,
            }
            statuses = [s for s in raw if s in allowed]
        else:
            statuses = [
                OnlineOrder.Status.PENDING,
                OnlineOrder.Status.ACCEPTED,
                OnlineOrder.Status.OUT_FOR_DELIVERY,
                OnlineOrder.Status.DELIVERED,
            ]

        orders = OnlineOrder.objects.filter(status__in=statuses).order_by("-created_at")

        payload = []
        for order in orders:
            items = order.items_json.get("items") if isinstance(order.items_json, dict) else order.items_json
            customer = {}
            if isinstance(order.items_json, dict):
                customer = order.items_json.get("customer") or {}
            payload.append(
                {
                    "order_id": order.id,
                    "status": order.status,
                    "items": items,
                    "customer": customer,
                    "estimated_total": str(order.estimated_total),
                    "final_total": str(order.final_total) if order.final_total is not None else None,
                    "created_at": order.created_at,
                    "expected_delivery_text": order.expected_delivery_text,
                    "expected_delivery_start": order.expected_delivery_start,
                    "expected_delivery_end": order.expected_delivery_end,
                    "delivery_slot_label": order.delivery_slot_label,
                    "delivery_slot_start": order.delivery_slot_start,
                    "delivery_slot_end": order.delivery_slot_end,
                    "delivery_slot_text": order.delivery_slot_text,
                    "delivery_date": order.delivery_date,
                    "out_for_delivery_at": order.out_for_delivery_at,
                    "delivered_at": order.delivered_at,
                    "delivered_by": order.delivered_by.username if order.delivered_by else None,
                }
            )

        return Response({"orders": payload})


class OrderDecisionView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        now = timezone.now()

        order = OnlineOrder.objects.filter(id=data["order_id"]).first()
        if not order:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        decision = data["decision"]
        if decision == "ACCEPT":
            delivery_label = data.get("delivery_slot_label", "")
            delivery_start = data.get("delivery_slot_start", "")
            delivery_end = data.get("delivery_slot_end", "")
            delivery_text = data.get("delivery_slot_text", "")
            delivery_date = data.get("delivery_date")
            out_for_delivery = bool(data.get("out_for_delivery"))

            items = order.items_json.get("items") if isinstance(order.items_json, dict) else order.items_json
            with transaction.atomic():
                if items:
                    external_ids = []
                    for item in items:
                        if isinstance(item, dict):
                            external_id = item.get("product_external_id")
                            if external_id:
                                external_ids.append(external_id)

                    products = Product.objects.filter(external_id__in=external_ids)
                    product_map = {p.external_id: p for p in products}

                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        external_id = item.get("product_external_id")
                        qty = Decimal(str(item.get("qty", "0") or "0"))
                        if not external_id or qty <= 0:
                            continue
                        product = product_map.get(external_id)
                        if not product:
                            if not settings.ALLOW_BACKORDERS:
                                return Response(
                                    {"error": f"Product not found for {external_id}"},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                            continue

                        batches = (
                            ProductBatch.objects.select_for_update()
                            .filter(product=product, qty_available__gt=0)
                            .order_by("created_at")
                        )
                        remaining = qty

                        for batch in batches:
                            if remaining <= 0:
                                break
                            take = remaining if batch.qty_available >= remaining else batch.qty_available
                            batch.qty_available = max(Decimal("0"), batch.qty_available - take)
                            batch.updated_at = now
                            batch.save(update_fields=["qty_available", "updated_at"])
                            remaining -= take

                        if remaining > 0 and not settings.ALLOW_BACKORDERS:
                            return Response(
                                {"error": f"Insufficient stock for {external_id}"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                        # Update aggregate inventory
                        total_qty = (
                            ProductBatch.objects.filter(product=product)
                            .aggregate(total=models.Sum("qty_available"))
                            .get("total")
                            or Decimal("0")
                        )
                        Inventory.objects.update_or_create(
                            product=product,
                            defaults={"qty_available": total_qty, "updated_at": now},
                        )

                order.status = (
                    OnlineOrder.Status.OUT_FOR_DELIVERY
                    if out_for_delivery
                    else OnlineOrder.Status.ACCEPTED
                )
                order.accepted_at = now
                order.synced_to_desktop_at = now
                if items:
                    total = Decimal("0")
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        line_total = item.get("line_total")
                        if line_total is None:
                            qty = Decimal(str(item.get("qty", "0") or "0"))
                            unit_price = Decimal(str(item.get("unit_price", "0") or "0"))
                            line_total = qty * unit_price
                        total += Decimal(str(line_total))
                    order.final_total = total
                else:
                    order.final_total = data.get("final_total", order.estimated_total)
                order.delivery_slot_label = delivery_label or order.delivery_slot_label
                order.delivery_slot_start = delivery_start or order.delivery_slot_start
                order.delivery_slot_end = delivery_end or order.delivery_slot_end
                order.delivery_slot_text = delivery_text or order.delivery_slot_text
                if delivery_date:
                    order.delivery_date = delivery_date
                    # Clear stale expected text once a real date is assigned
                    order.expected_delivery_text = ""
                if out_for_delivery:
                    order.out_for_delivery_at = now
                if "pricing_breakdown" in data:
                    order.pricing_breakdown_json = data["pricing_breakdown"]
                order.save()
        else:
            order.status = OnlineOrder.Status.REJECTED
            order.rejected_at = now
            reason = data.get("reason")
            if reason:
                if isinstance(order.items_json, dict):
                    order.items_json["decision_reason"] = reason
                else:
                    order.items_json = {"items": order.items_json, "decision_reason": reason}
            order.save()

        return Response({"status": order.status})


class OrderStatusUpdateView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        now = timezone.now()

        order = OnlineOrder.objects.filter(id=data["order_id"]).first()
        if not order:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if data["status"] == "OUT_FOR_DELIVERY":
            order.status = OnlineOrder.Status.OUT_FOR_DELIVERY
            order.out_for_delivery_at = now
            order.save()

        return Response({"status": order.status})

class SyncSalesView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sales = RetailTransaction.objects.all().order_by("-date")
        payload = []
        for sale in sales:
            payload.append(
                {
                    "desktop_id": sale.desktop_id,
                    "customer_phone": str(sale.customer.phone) if sale.customer else None,
                    "customer_name": sale.customer.name if sale.customer else None,
                    "date": sale.date,
                    "grand_total": str(sale.grand_total),
                    "payment_status": sale.payment_status,
                    "items_json": sale.items_json,
                }
            )
        return Response({"sales": payload})

    def post(self, request):
        serializer = SyncSalesPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        mode = payload["mode"]
        sales_data = payload["sales"]

        desktop_ids = [s["desktop_id"] for s in sales_data]
        existing = RetailTransaction.objects.filter(desktop_id__in=desktop_ids)
        existing_map = {t.desktop_id: t for t in existing}

        phones = [s["customer_phone"] for s in sales_data if s.get("customer_phone")]
        customers = Customer.objects.filter(phone__in=phones)
        customer_map = {str(c.phone): c for c in customers}

        to_create = []
        to_update = []

        for data in sales_data:
            desktop_id = data["desktop_id"]
            phone = str(data.get("customer_phone", "")).strip()
            customer = customer_map.get(phone)

            if desktop_id in existing_map:
                txn = existing_map[desktop_id]
                txn.customer = customer
                txn.date = data["date"]
                txn.grand_total = data["grand_total"]
                txn.payment_status = data["payment_status"]
                txn.items_json = data["items_json"]
                to_update.append(txn)
            else:
                to_create.append(
                    RetailTransaction(
                        desktop_id=desktop_id,
                        customer=customer,
                        date=data["date"],
                        grand_total=data["grand_total"],
                        payment_status=data["payment_status"],
                        items_json=data["items_json"],
                    )
                )

        with transaction.atomic():
            if to_create:
                RetailTransaction.objects.bulk_create(to_create)
            if to_update:
                RetailTransaction.objects.bulk_update(
                    to_update,
                    ["customer", "date", "grand_total", "payment_status", "items_json"],
                )

        return Response({"created": len(to_create), "updated": len(to_update), "mode": mode})


class SyncResetView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncResetPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        now = timezone.now()

        products_data = payload["products"]
        inventory_data = payload["inventory"]

        with transaction.atomic():
            Inventory.objects.all().delete()
            Product.objects.all().delete()

            # Products
            product_objects = []
            for data in products_data:
                product_objects.append(
                    Product(
                        external_id=data["external_id"],
                        name=data["name"],
                        sku=data.get("sku", ""),
                        price_estimate=data["price_estimate"],
                        hsn_code=data["hsn_code"],
                        gst_rate=data["gst_rate"],
                        is_active=data.get("is_active", True),
                        updated_at=data.get("updated_at") or now,
                    )
                )
            if product_objects:
                Product.objects.bulk_create(product_objects)

            products = Product.objects.all()
            product_map = {p.external_id: p for p in products}

            # Inventory
            inventory_objects = []
            for data in inventory_data:
                product = product_map.get(data["product_external_id"])
                if product is None:
                    continue
                inventory_objects.append(
                    Inventory(
                        product=product,
                        qty_available=data["qty_available"],
                        updated_at=data.get("updated_at") or now,
                    )
                )
            if inventory_objects:
                Inventory.objects.bulk_create(inventory_objects)

        return Response(
            {
                "products": len(products_data),
                "inventory": len(inventory_data),
                "status": "reset",
            }
        )


class SyncConfigView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = ShopConfig.get()
        return Response(
            {
                "require_delivery_photo": config.require_delivery_photo,
            }
        )

    def post(self, request):
        serializer = DeliverySettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = ShopConfig.get()
        config.require_delivery_photo = serializer.validated_data[
            "require_delivery_photo"
        ]
        config.save(update_fields=["require_delivery_photo"])
        return Response(
            {"require_delivery_photo": config.require_delivery_photo},
            status=status.HTTP_200_OK,
        )


class DeliveryAgentCreateView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeliveryAgentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        username = data["username"].strip()
        password = data["password"]
        full_name = data["full_name"].strip().title()

        if not username.isdigit() or len(username) != 10:
            return Response(
                {"error": "Phone number must be 10 digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parts = full_name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        group, _ = Group.objects.get_or_create(name="delivery_agents")
        user.groups.add(group)

        return Response(
            {
                "id": user.id,
                "username": user.username,
            },
            status=status.HTTP_201_CREATED,
        )


class DeliveryAgentListView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        group = Group.objects.filter(name="delivery_agents").first()
        if not group:
            return Response({"agents": []})

        users = (
            User.objects.filter(groups=group)
            .order_by("username")
        )
        payload = []
        for u in users:
            payload.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "full_name": f"{u.first_name} {u.last_name}".strip(),
                    "is_active": u.is_active,
                    "last_login": u.last_login,
                }
            )
        return Response({"agents": payload})


class DeliveryAgentUpdateView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeliveryAgentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = None
        if "id" in data:
            user = User.objects.filter(id=data["id"]).first()
        elif "username" in data:
            user = User.objects.filter(username=data["username"]).first()

        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.groups.filter(name="delivery_agents").exists():
            return Response({"error": "User is not a delivery agent."}, status=status.HTTP_400_BAD_REQUEST)

        if "password" in data and data["password"]:
            user.set_password(data["password"])

        if "is_active" in data:
            user.is_active = data["is_active"]

        user.save()

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "is_active": user.is_active,
            }
        )


class DeliveryAgentDeleteView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeliveryAgentDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = None
        if "id" in data:
            user = User.objects.filter(id=data["id"]).first()
        elif "username" in data:
            user = User.objects.filter(username=data["username"]).first()

        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.groups.filter(name="delivery_agents").exists():
            return Response({"error": "User is not a delivery agent."}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({"status": "deleted"})


class SyncCategoriesView(APIView):
    """Receives categories from the desktop app and upserts them into the webfront DB."""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncCategoriesPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        mode = payload["mode"]
        categories_data = payload["categories"]

        created = 0
        updated = 0

        with transaction.atomic():
            external_ids = [c["id"] for c in categories_data]
            existing = Category.objects.filter(external_id__in=external_ids)
            existing_map = {c.external_id: c for c in existing}

            to_create = []
            to_update = []

            for data in categories_data:
                ext_id = data["id"]
                name = data["name"]
                raw_img = (data.get("image_data") or "").strip()

                # Strip data URI prefix if present
                if raw_img.startswith("data:") and "base64," in raw_img:
                    raw_img = raw_img.split("base64,", 1)[1]

                if ext_id in existing_map:
                    cat = existing_map[ext_id]
                    cat.name = name
                    if raw_img:
                        cat.image_b64 = raw_img
                    to_update.append(cat)
                    updated += 1
                else:
                    to_create.append(
                        Category(
                            external_id=ext_id,
                            name=name,
                            image_b64=raw_img,
                        )
                    )
                    created += 1

            if to_create:
                Category.objects.bulk_create(to_create)
            if to_update:
                Category.objects.bulk_update(to_update, ["name", "image_b64"])

            if mode == "full":
                Category.objects.exclude(external_id__in=external_ids).delete()

        return Response({"created": created, "updated": updated, "mode": mode})

