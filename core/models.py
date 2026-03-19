import secrets
from django.db import models


class ShopConfig(models.Model):
    """
    Singleton model — only one row should ever exist.
    Stores shop-wide settings including the API key for
    the Flutter desktop app to use when syncing.
    """
    shop_name = models.CharField(max_length=200, default="My Shop")
    api_key = models.CharField(
        max_length=128,
        help_text="Copy this key into the Flutter desktop app to enable sync.",
    )
    allow_backorders = models.BooleanField(default=False)
    require_delivery_photo = models.BooleanField(
        default=False,
        help_text="Require delivery agents to upload at least one proof photo before completing delivery.",
    )
    shop_template = models.CharField(
        max_length=64,
        choices=[
            ("default", "Default Theme"),
            ("modern", "Modern Theme"),
        ],
        default="default",
        help_text="Select the visual theme for the storefront.",
    )

    class Meta:
        verbose_name = "Shop Configuration"
        verbose_name_plural = "Shop Configuration"

    def __str__(self):
        return self.shop_name

    def save(self, *args, **kwargs):
        # Enforce singleton — only one config row allowed
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "api_key": secrets.token_urlsafe(32),
            },
        )
        return obj
