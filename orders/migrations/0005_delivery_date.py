from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_merge_0002_delivery_slots_0003_retailtransaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="onlineorder",
            name="delivery_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
