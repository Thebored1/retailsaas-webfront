from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="onlineorder",
            name="expected_delivery_text",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="onlineorder",
            name="expected_delivery_start",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="onlineorder",
            name="expected_delivery_end",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="onlineorder",
            name="delivery_slot_label",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="onlineorder",
            name="delivery_slot_start",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="onlineorder",
            name="delivery_slot_end",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="onlineorder",
            name="delivery_slot_text",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="onlineorder",
            name="out_for_delivery_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
