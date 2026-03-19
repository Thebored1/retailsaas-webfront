from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_shopconfig_shop_template"),
    ]

    operations = [
        migrations.AddField(
            model_name="shopconfig",
            name="require_delivery_photo",
            field=models.BooleanField(
                default=False,
                help_text="Require delivery agents to upload at least one proof photo before completing delivery.",
            ),
        ),
    ]
