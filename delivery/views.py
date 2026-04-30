from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import ShopConfig
from orders.models import OnlineOrder, DeliveryProof


DELIVERY_GROUP_NAME = "delivery_agents"

PHONE_INPUT_ATTRS = {
    "type": "tel",
    "inputmode": "numeric",
    "maxlength": "10",
    "pattern": "[0-9]{10}",
    "autocomplete": "tel",
    "title": "Enter a 10-digit phone number",
    "oninput": "this.value=this.value.replace(/\\D/g,'').slice(0,10)",
}


class DeliveryLoginForm(forms.Form):
    phone = forms.IntegerField(
        min_value=1000000000,
        max_value=9999999999,
        label="Phone Number",
        widget=forms.TextInput(attrs={**PHONE_INPUT_ATTRS, "placeholder": "Enter your registered phone"}),
    )
    password = forms.CharField(widget=forms.PasswordInput)


def _theme_template(template_name: str) -> str:
    try:
        base = ShopConfig.get().shop_template
    except Exception:
        base = "default"
    return f"themes/{base}/{template_name}"


def _is_delivery_agent(user) -> bool:
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=DELIVERY_GROUP_NAME).exists()


def _require_delivery_agent(request):
    if not _is_delivery_agent(request.user):
        messages.error(request, "You do not have access to the delivery console.")
        logout(request)
        return redirect("delivery_login")
    return None


def delivery_login(request):
    if request.user.is_authenticated and _is_delivery_agent(request.user):
        return redirect("delivery_orders")

    form = DeliveryLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        phone = str(form.cleaned_data["phone"])
        password = form.cleaned_data["password"]
        from django.contrib.auth import authenticate

        user = authenticate(request, username=phone, password=password)
        if user is None:
            messages.error(request, "Invalid phone number or password.")
            return render(request, _theme_template("delivery/login.html"), {"form": form})
        if not _is_delivery_agent(user):
            messages.error(request, "This account is not a delivery agent.")
            return redirect("delivery_login")
        login(request, user)
        return redirect("delivery_orders")

    return render(request, _theme_template("delivery/login.html"), {"form": form})


def delivery_logout(request):
    logout(request)
    return redirect("delivery_login")


@login_required(login_url='delivery_login')
def delivery_orders_list(request):
    gate = _require_delivery_agent(request)
    if gate:
        return gate

    from django.db.models import Q
    orders = OnlineOrder.objects.filter(
        Q(status=OnlineOrder.Status.OUT_FOR_DELIVERY) |
        Q(status=OnlineOrder.Status.DELIVERED)
    ).order_by("-delivered_at", "delivery_date", "created_at")

    return render(
        request,
        _theme_template("delivery/orders_list.html"),
        {
            "orders": orders,
        },
    )


@login_required(login_url='delivery_login')
def delivery_order_detail(request, order_id: int):
    gate = _require_delivery_agent(request)
    if gate:
        return gate

    order = get_object_or_404(OnlineOrder, id=order_id)
    require_photo = ShopConfig.get().require_delivery_photo

    items = []
    customer = {}
    if isinstance(order.items_json, dict):
        items = order.items_json.get("items", []) or []
        customer = order.items_json.get("customer", {}) or {}
    elif isinstance(order.items_json, list):
        items = order.items_json

    normalized_items = []
    for item in items:
        if isinstance(item, dict):
            name = (
                item.get("product_name")
                or item.get("productName")
                or item.get("name")
                or "Item"
            )
            qty = item.get("qty") or item.get("quantity") or 1
            normalized_items.append(
                {
                    "name": name,
                    "qty": qty,
                    "line_total": item.get("line_total"),
                    "batch_allocations": item.get("batch_allocations") or [],
                }
            )
        else:
            normalized_items.append({"name": str(item), "qty": 1})

    if request.method == "POST":
        if order.status != OnlineOrder.Status.OUT_FOR_DELIVERY:
            messages.error(request, "Only orders out for delivery can be completed.")
            return redirect("delivery_order_detail", order_id=order.id)

        files = request.FILES.getlist("photos")
        if require_photo and not files:
            messages.error(request, "At least one delivery photo is required.")
            return redirect("delivery_order_detail", order_id=order.id)

        for f in files:
            DeliveryProof.objects.create(
                order=order,
                image=f,
                uploaded_by=request.user,
            )

        order.status = OnlineOrder.Status.DELIVERED
        order.delivered_at = timezone.now()
        order.delivered_by = request.user
        order.save(update_fields=["status", "delivered_at", "delivered_by"])

        messages.success(request, "Delivery completed successfully.")
        return redirect("delivery_order_detail", order_id=order.id)

    return render(
        request,
        _theme_template("delivery/order_detail.html"),
        {
            "order": order,
            "items": normalized_items,
            "customer": customer,
            "require_photo": require_photo,
            "photos": order.delivery_proofs.all().order_by("-uploaded_at"),
        },
    )
