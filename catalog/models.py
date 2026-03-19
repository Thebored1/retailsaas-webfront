from django.db import models


class Category(models.Model):
    external_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    external_id = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=120, blank=True)
    
    # Store the actual image file on the Django server
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    mrp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    uom = models.CharField(max_length=32, blank=True, help_text="Unit of measure (e.g. pcs, kg)")
    
    hsn_code = models.CharField(max_length=64, blank=True)
    gst_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.name


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    qty_available = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.product.name} - {self.qty_available}"


class ProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    external_id = models.CharField(max_length=64, unique=True)
    batch_number = models.CharField(max_length=64, blank=True, default="")
    expiry_date = models.DateField(null=True, blank=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qty_available = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.product.name} - {self.batch_number or self.external_id}"
