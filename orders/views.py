from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from catalog.models import Product, Inventory, ProductBatch
from .models import OnlineOrder


def _theme_template(template_name: str) -> str:
    try:
        from core.models import ShopConfig
        base = ShopConfig.get().shop_template
    except Exception:
        base = "default"
    return f"themes/{base}/{template_name}"


def _get_cart(request):
    return request.session.get("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True

def _expected_delivery_window():
    tomorrow = timezone.localdate() + timedelta(days=1)
    return {
        "text": "Tomorrow, 9 AM - 12 PM",
        "start": "09:00",
        "end": "12:00",
        "date": tomorrow,
    }


def _get_fifo_batches(product):
    return ProductBatch.objects.filter(
        product=product, qty_available__gt=0
    ).order_by("created_at")


def _allocate_batches(product, qty, allow_backorders=False):
    remaining = Decimal(qty)
    allocations = []
    fifo_batches = _get_fifo_batches(product)
    fallback_price = (
        fifo_batches.first().selling_price
        if fifo_batches.exists()
        else Decimal(product.price_estimate)
    )

    for batch in fifo_batches:
        if remaining <= 0:
            break
        take = remaining if batch.qty_available >= remaining else batch.qty_available
        allocations.append(
            {
                "batch_id": batch.external_id,
                "qty": float(take),
                "unit_price": str(batch.selling_price),
            }
        )
        remaining -= take

    if remaining > 0 and allow_backorders:
        allocations.append(
            {
                "batch_id": None,
                "qty": float(remaining),
                "unit_price": str(fallback_price),
            }
        )
        remaining = Decimal("0")

    return allocations, remaining


def add_to_cart(request, product_id):
    if request.method != "POST":
        return redirect("product_detail", product_id=product_id)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    qty = int(request.POST.get("qty", "1"))
    if qty < 1:
        qty = 1

    inventory = Inventory.objects.filter(product=product).first()
    qty_available = inventory.qty_available if inventory else Decimal("0")

    if not settings.ALLOW_BACKORDERS and qty_available < qty:
        messages.error(request, "Not enough stock available for this item.")
        return redirect("product_detail", product_id=product_id)

    cart = _get_cart(request)
    cart_key = str(product_id)
    cart[cart_key] = cart.get(cart_key, 0) + qty
    _save_cart(request, cart)
    return redirect("cart_view")


def cart_view(request):
    cart = _get_cart(request)
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids, is_active=True)
    inventory_map = {
        inv.product_id: inv.qty_available
        for inv in Inventory.objects.filter(product__in=products)
    }

    items = []
    estimated_total = Decimal("0")
    for product in products:
        qty = int(cart.get(str(product.id), 0))
        allocations, _remaining = _allocate_batches(
            product, qty, allow_backorders=settings.ALLOW_BACKORDERS
        )
        line_total = Decimal("0")
        for alloc in allocations:
            line_total += Decimal(alloc["unit_price"]) * Decimal(str(alloc["qty"]))
        if line_total == 0 and qty > 0:
            line_total = Decimal(product.price_estimate) * Decimal(qty)
            if not allocations:
                allocations = [
                    {
                        "batch_id": None,
                        "qty": float(qty),
                        "unit_price": str(product.price_estimate),
                    }
                ]
        estimated_total += line_total
        items.append(
            {
                "product": product,
                "qty": qty,
                "line_total": line_total,
                "qty_available": inventory_map.get(product.id, Decimal("0")),
                "batch_allocations": allocations,
            }
        )

    expected_delivery = _expected_delivery_window()
    context = {
        "items": items,
        "estimated_total": estimated_total,
        "allow_backorders": settings.ALLOW_BACKORDERS,
        "expected_delivery_text": expected_delivery["text"],
    }
    return render(request, _theme_template("cart.html"), context)


def update_cart(request, product_id):
    if request.method != "POST":
        return redirect("cart_view")
    cart = _get_cart(request)
    qty = int(request.POST.get("qty", "1"))
    if qty < 1:
        cart.pop(str(product_id), None)
    else:
        if not settings.ALLOW_BACKORDERS:
            product = get_object_or_404(Product, id=product_id, is_active=True)
            inventory = Inventory.objects.filter(product=product).first()
            qty_available = inventory.qty_available if inventory else Decimal("0")
            if qty_available <= 0:
                cart.pop(str(product_id), None)
                messages.error(request, "This item is out of stock.")
                _save_cart(request, cart)
                return redirect("cart_view")
            if qty > qty_available:
                qty = int(qty_available)
                messages.error(
                    request,
                    "Quantity reduced to available stock.",
                )
        cart[str(product_id)] = qty
    _save_cart(request, cart)
    return redirect("cart_view")


def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    _save_cart(request, cart)
    return redirect("cart_view")


def checkout_view(request):
    cart = _get_cart(request)
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids, is_active=True)
    inventory_map = {
        inv.product_id: inv.qty_available
        for inv in Inventory.objects.filter(product__in=products)
    }

    items = []
    estimated_total = Decimal("0")
    can_checkout = True
    for product in products:
        qty = int(cart.get(str(product.id), 0))
        qty_available = inventory_map.get(product.id, Decimal("0"))
        if not settings.ALLOW_BACKORDERS and qty_available < qty:
            can_checkout = False
        allocations, remaining = _allocate_batches(
            product, qty, allow_backorders=settings.ALLOW_BACKORDERS
        )
        if remaining > 0 and not settings.ALLOW_BACKORDERS:
            can_checkout = False
        line_total = Decimal("0")
        for alloc in allocations:
            line_total += Decimal(alloc["unit_price"]) * Decimal(str(alloc["qty"]))
        if line_total == 0 and qty > 0:
            line_total = Decimal(product.price_estimate) * Decimal(qty)
            if not allocations:
                allocations = [
                    {
                        "batch_id": None,
                        "qty": float(qty),
                        "unit_price": str(product.price_estimate),
                    }
                ]
        estimated_total += line_total
        items.append(
            {
                "product": product,
                "qty": qty,
                "line_total": line_total,
                "qty_available": qty_available,
                "batch_allocations": allocations,
            }
        )

    expected_delivery = _expected_delivery_window()
    if request.method == "POST":
        if not can_checkout or not items:
            messages.error(request, "Cannot place order with insufficient stock.")
            return redirect("checkout_view")

        customer_profile = None
        if request.user.is_authenticated and hasattr(request.user, 'customer'):
            customer_profile = request.user.customer
        else:
            # Create a guest customer profile if they provided info
            phone = request.POST.get("customer_phone", "")
            if phone:
                phone = phone.strip()
                if not phone.isdigit() or len(phone) != 10:
                    messages.error(request, "Phone number must be exactly 10 digits.")
                    return redirect("checkout_view")
                from customers.models import Customer
                try:
                    # check if guest profile already exists or create new
                    customer_profile, created = Customer.objects.get_or_create(
                        phone=int(phone),
                        defaults={
                            'name': request.POST.get("customer_name", "").title(),
                            'email': request.POST.get("customer_email", ""),
                            'address': request.POST.get("customer_address", "")
                        }
                    )
                except Exception:
                    pass

        customer_json = {
            "name": request.POST.get("customer_name", ""),
            "phone": request.POST.get("customer_phone", "").strip(),
            "email": request.POST.get("customer_email", ""),
            "address": request.POST.get("customer_address", ""),
        }

        order_items = []
        for item in items:
            product = item["product"]
            unit_price = (
                (item["line_total"] / Decimal(item["qty"]))
                if item["qty"] > 0
                else Decimal("0")
            )
            order_items.append(
                {
                    "product_external_id": product.external_id,
                    "product_name": product.name,
                    "qty": item["qty"],
                    "unit_price": str(unit_price),
                    "line_total": str(item["line_total"]),
                    "batch_allocations": item["batch_allocations"],
                }
            )

        order = OnlineOrder.objects.create(
            customer=customer_profile,
            status=OnlineOrder.Status.PENDING,
            items_json={"items": order_items, "customer": customer_json},
            estimated_total=estimated_total,
            expected_delivery_text=expected_delivery["text"],
            expected_delivery_start=expected_delivery["start"],
            expected_delivery_end=expected_delivery["end"],
        )

        _save_cart(request, {})
        return redirect("order_submitted", order_id=order.id)

    context = {
        "items": items,
        "estimated_total": estimated_total,
        "allow_backorders": settings.ALLOW_BACKORDERS,
        "can_checkout": can_checkout,
        "expected_delivery_text": expected_delivery["text"],
    }
    return render(request, _theme_template("checkout.html"), context)


def order_submitted(request, order_id):
    order = get_object_or_404(OnlineOrder, id=order_id)
    items = []
    if isinstance(order.items_json, dict):
        items = order.items_json.get("items", []) or []
    elif isinstance(order.items_json, list):
        items = order.items_json
    context = {"order": order, "items": items}
    return render(request, _theme_template("order_submitted.html"), context)
