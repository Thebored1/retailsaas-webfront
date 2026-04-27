from django.conf import settings
from django.shortcuts import get_object_or_404, render
from decimal import Decimal
from core.models import ShopConfig
from .models import Product, Inventory, Category, ProductBatch


def _theme_template(template_name: str) -> str:
    try:
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
    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    categories = Category.objects.all().order_by('name')
    products = Product.objects.filter(is_active=True)
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if query:
        products = products.filter(name__icontains=query)

    if min_price:
        products = products.filter(price_estimate__gte=min_price)
    
    if max_price:
        products = products.filter(price_estimate__lte=max_price)
        
    sort = request.GET.get('sort', 'price_high_low')
    
    if sort == 'newest':
        products = products.order_by("-updated_at")
    elif sort == 'price_low_high':
        products = products.order_by("price_estimate")
    elif sort == 'price_high_low':
        products = products.order_by("-price_estimate")
    else:
        products = products.order_by("name")
    
    inventory = _inventory_map(products)
    fifo_price_map = _fifo_batch_price_map(products)

    # Featured products for the homepage "Trending Now" section — first 8 active
    featured_qs = Product.objects.filter(is_active=True).order_by("-updated_at")[:8]
    featured_inventory = _inventory_map(featured_qs)
    featured_price_map = _fifo_batch_price_map(featured_qs)

    is_filtering = any([category_id, query, min_price, max_price])

    context = {
        "products": products,
        "categories": categories,
        "current_category": int(category_id) if category_id and category_id.isdigit() else None,
        "query": query,
        "min_price": min_price,
        "max_price": max_price,
        "is_filtering": is_filtering,
        "current_sort": sort,
        "inventory": inventory,
        "allow_backorders": settings.ALLOW_BACKORDERS,
        "fifo_price_map": fifo_price_map,
        # Homepage featured strip
        "featured_products": featured_qs,
        "featured_inventory": featured_inventory,
        "featured_price_map": featured_price_map,
    }
    template_name = "product_list.html"
    config = ShopConfig.get()
    theme = config.shop_template or "default"
    
    if is_filtering and theme == "squareshoppe":
        # Use a specialized results page if search/filters are active for this theme
        template_name = "search_results.html"
        
    return render(request, f"themes/{theme}/{template_name}", context)


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
    # Fetch related products for the carousel (same category if possible, or just recent)
    related_qs = Product.objects.filter(is_active=True).exclude(id=product.id)
    if product.category:
        related_qs = related_qs.filter(category=product.category) | related_qs.exclude(category=product.category)
    
    related_products = related_qs.distinct().order_by('?')[:10]
    related_inventory = _inventory_map(related_products)
    related_price_map = _fifo_batch_price_map(related_products)

    context = {
        "product": product,
        "qty_available": qty_available,
        "allow_backorders": settings.ALLOW_BACKORDERS,
        "fifo_price": fifo_price,
        "lowest_price": lowest_price,
        "lowest_qty": lowest_qty,
        "other_stock": other_stock,
        # Carousel data
        "related_products": related_products,
        "related_inventory": related_inventory,
        "related_price_map": related_price_map,
    }
    return render(request, _theme_template("product_detail.html"), context)
