from django.contrib import admin
from django.utils.html import format_html
from .models import ShopConfig


@admin.register(ShopConfig)
class ShopConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Shop Details", {
            "fields": (
                "shop_name",
                "shop_template",
                "allow_backorders",
                "require_delivery_photo",
            ),
        }),
        ("Desktop App API Key", {
            "fields": ("api_key", "api_key_display"),
            "description": (
                "Copy the API key below into the Flutter desktop app "
                "under Settings → Server Connection."
            ),
        }),
    )
    readonly_fields = ("api_key_display",)

    def api_key_display(self, obj):
        return format_html(
            '<code style="'
            "background:#1e1e1e;color:#4fc3f7;padding:8px 14px;"
            "border-radius:6px;font-size:14px;letter-spacing:1px;"
            'display:inline-block;margin-top:4px">{}</code>'
            '<p style="margin-top:6px;color:#888;font-size:12px">'
            "⚠ Changing the key above will disconnect the desktop app until updated there too."
            "</p>",
            obj.api_key,
        )
    api_key_display.short_description = "Key Preview"

    def has_add_permission(self, request):
        # Only one config row allowed
        return not ShopConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def get_object(self, request, object_id, from_field=None):
        # Always redirect to the singleton row
        return ShopConfig.get()

    def changelist_view(self, request, extra_context=None):
        # Skip the list view — go straight to the edit page
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        obj = ShopConfig.get()
        return HttpResponseRedirect(
            reverse("admin:core_shopconfig_change", args=[obj.pk])
        )
