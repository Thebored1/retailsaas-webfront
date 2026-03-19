from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_category_product_image_product_mrp_product_uom_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(max_length=64, unique=True)),
                ("batch_number", models.CharField(blank=True, default="", max_length=64)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("selling_price", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("qty_available", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("created_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "product",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="catalog.product"),
                ),
            ],
        ),
    ]
