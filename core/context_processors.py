from core.models import ShopConfig

def shop_context(request):
    """
    Injects the global shop configuration into all templates
    so they can display the shop name and proper CSS.
    """
    try:
        config = ShopConfig.get()
        theme = config.shop_template or "default"
        return {
            "shop_name": config.shop_name,
            "theme_css_path": f"themes/{theme}/theme.css",
            "theme_template": theme,
            "theme_base_template": f"themes/{theme}/base.html",
        }
    except Exception:
        # Fallback if DB is not ready during migrations
        return {
            "shop_name": "My Shop",
            "theme_css_path": "themes/default/theme.css",
            "theme_template": "default",
            "theme_base_template": "themes/default/base.html",
        }
