from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_delivery_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="retailtransaction",
            name="desktop_id",
            field=models.CharField(default=uuid.uuid4, max_length=64, unique=True),
        ),
    ]
