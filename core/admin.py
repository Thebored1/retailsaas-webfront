from django.contrib import admin
from django.utils.html import format_html
from .models import ShopConfig, HeroSlide


class HeroSlideInline(admin.StackedInline):
    model = HeroSlide
    extra = 1
    fields = (
        ("tagline", "highlight"),
        "subtext",
        ("button_label", "button_url"),
        "image",
        "order"
    )
    sortable_field_name = "order"


@admin.register(ShopConfig)
class ShopConfigAdmin(admin.ModelAdmin):
    inlines = [HeroSlideInline]

    class Media:
        css = {
            'all': ('core/admin/shop_config.css',)
        }
        js = ('core/admin/shop_config.js',)

    fieldsets = (
        # ── 1. Shop Identity & Behavior ───────────────────────────────────
        ("🏬 Shop", {
            "fields": (
                ("shop_name", "logo_text", "logo"),
                "shop_template",
                "show_top_bar",
                "top_bar_offer",
                "store_address",
                ("support_email", "support_phone"),
                ("allow_backorders", "require_delivery_photo"),
            ),
            "description": "General store settings and identity.",
        }),

        # ── 2. Slides ──────────────────────────────────────────────────────
        ("🖼️ Hero Slides", {
            "fields": (), # The Inline will be shown here by JS
            "description": "Manage the rotating banners at the top of your homepage.",
        }),

        # ── 3. Promo Banner ────────────────────────────────────────────────
        ("🎁 Promo Banner", {
            "fields": (
                "show_promo_banner",
                "promo_badge",
                "promo_title",
                "promo_body",
                ("promo_button_label", "promo_button_url"),
                "promo_image",
            ),
            "description": "The full-width promotional banner section below the categories grid.",
        }),

        # ── 4. Benefits & Newsletter ───────────────────────────────────────
        ("✨ Extra Sections", {
            "fields": (
                "show_benefits",
                "show_sidebar_promo",
                ("sidebar_promo_title", "sidebar_promo_icon"),
                "sidebar_promo_body",
                "show_newsletter",
                "newsletter_title",
                "newsletter_body",
            ),
            "description": "Toggle and configure optional homepage and sidebar sections.",
        }),

        # ── 5. Navigation Links ────────────────────────────────────────────
        ("🧭 Navigation", {
            "fields": (
                ("nav_link_1_label", "nav_link_1_url"),
                ("nav_link_2_label", "nav_link_2_url"),
                ("nav_link_3_label", "nav_link_3_url"),
                ("nav_link_4_label", "nav_link_4_url"),
            ),
            "description": "Custom links for the top navigation bar.",
        }),

        # ── 6. Footer ─────────────────────────────────────────────────────
        ("🦶 Footer", {
            "fields": (
                "footer_tagline",
                "footer_col2_heading",
                ("footer_col2_link_1_label", "footer_col2_link_1_url"),
                ("footer_col2_link_2_label", "footer_col2_link_2_url"),
                ("footer_col2_link_3_label", "footer_col2_link_3_url"),
                ("footer_col2_link_4_label", "footer_col2_link_4_url"),
                "footer_col3_heading",
                ("footer_col3_link_1_label", "footer_col3_link_1_url"),
                ("footer_col3_link_2_label", "footer_col3_link_2_url"),
                ("footer_col3_link_3_label", "footer_col3_link_3_url"),
                ("footer_col3_link_4_label", "footer_col3_link_4_url"),
                "footer_col4_heading",
                ("footer_col4_link_1_label", "footer_col4_link_1_url"),
                ("footer_col4_link_2_label", "footer_col4_link_2_url"),
                ("footer_col4_link_3_label", "footer_col4_link_3_url"),
                ("footer_col4_link_4_label", "footer_col4_link_4_url"),
            ),
            "description": "Content for the site footer.",
        }),

        # ── 7. Desktop App API Key ─────────────────────────────────────────
        ("🔑 API Sync", {
            "fields": ("api_key", "api_key_display"),
            "description": "Sync settings for the Flutter desktop app.",
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
