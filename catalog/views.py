from django.conf import settings
from django.shortcuts import get_object_or_404, render
from decimal import Decimal
from .models import Product, Inventory, Category, ProductBatch


def _theme_template(template_name: str) -> str:
    try:
        from core.models import ShopConfig
        base = ShopConfig.get().shop_template
    except Exception:
        base = "default"
    return f"themes/{base}/{template_name}"


def _inventory_map(products):
    inventory = Inventory.objects.filter(product__in=products)
    return {inv.product_id: inv.qty_available for inv in inventory}


def _fifo_batch_price_map(products):
    batches = (
        ProductBatch.objects.filter(product__in=products, qty_available__gt=0)
        .order_by("product_id", "created_at")
        .values("product_id", "selling_price")
    )
    price_map = {}
    for b in batches:
        if b["product_id"] not in price_map:
            price_map[b["product_id"]] = b["selling_price"]
    return price_map


def product_list(request):
    category_id = request.GET.get('category')
    categories = Category.objects.all().order_by('name')
    
    products = Product.objects.filter(is_active=True)
    if category_id:
        products = products.filter(category_id=category_id)
        
    products = products.order_by("name")
    
    inventory = _inventory_map(products)
    fifo_price_map = _fifo_batch_price_map(products)
    context = {
        "products": products,
        "categories": categories,
        "current_category": int(category_id) if category_id and category_id.isdigit() else None,
        "inventory": inventory,
        "allow_backorders": settings.ALLOW_BACKORDERS,
        "fifo_price_map": fifo_price_map,
    }
    return render(request, _theme_template("product_list.html"), context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    inventory = Inventory.objects.filter(product=product).first()
    qty_available = inventory.qty_available if inventory else Decimal("0")

    batches = ProductBatch.objects.filter(
        product=product, qty_available__gt=0
    ).order_by("created_at")
    fifo_price = batches.first().selling_price if batches.exists() else product.price_estimate
    lowest_batch = (
        batches.order_by("selling_price").first() if batches.exists() else None
    )
    lowest_price = lowest_batch.selling_price if lowest_batch else product.price_estimate
    lowest_qty = lowest_batch.qty_available if lowest_batch else Decimal("0")
    other_stock = qty_available - lowest_qty if qty_available > 0 else Decimal("0")
    context = {
        "product": product,
        "qty_available": qty_available,
        "allow_backorders": settings.ALLOW_BACKORDERS,
        "fifo_price": fifo_price,
        "lowest_price": lowest_price,
        "lowest_qty": lowest_qty,
        "other_stock": other_stock,
    }
    return render(request, _theme_template("product_detail.html"), context)
