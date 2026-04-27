from core.models import ShopConfig


def shop_context(request):
    """
    Injects the global shop configuration into all templates so they can
    display the shop name, theme CSS, and all content-managed sections
    (hero, promo banner, nav links, footer).
    """
    try:
        config = ShopConfig.get()
        theme = config.shop_template or "default"
        return {
            # ── Core ──────────────────────────────────────────────────────
            "shop_name": config.shop_name,
            "logo_text": config.logo_text or config.shop_name,
            "logo_url": config.logo.url if config.logo else None,
            "theme_css_path": f"themes/{theme}/theme.css",
            "theme_template": theme,
            "theme_base_template": f"themes/{theme}/base.html",

            # ── Top Bar ───────────────────────────────────────────────────
            "show_top_bar": config.show_top_bar,
            "top_bar_offer": config.top_bar_offer,
            "store_address": config.store_address,

            # ── Homepage — Hero ───────────────────────────────────────────
            "hero_slides": config.slides.all(),

            # ── Homepage — Promo ──────────────────────────────────────────
            "show_promo_banner": config.show_promo_banner,
            "promo_badge": config.promo_badge,
            "promo_title": config.promo_title,
            "promo_body": config.promo_body,
            "promo_button_label": config.promo_button_label,
            "promo_button_url": config.promo_button_url,
            "promo_image": config.promo_image,

            # ── Homepage — Extra ──────────────────────────────────────────
            "show_benefits": config.show_benefits,
            "show_sidebar_promo": config.show_sidebar_promo,
            "sidebar_promo_title": config.sidebar_promo_title,
            "sidebar_promo_body": config.sidebar_promo_body,
            "sidebar_promo_icon": config.sidebar_promo_icon,
            "benefit_1_title": config.benefit_1_title,
            "benefit_1_subtext": config.benefit_1_subtext,
            "benefit_1_icon": config.benefit_1_icon,
            "benefit_2_title": config.benefit_2_title,
            "benefit_2_subtext": config.benefit_2_subtext,
            "benefit_2_icon": config.benefit_2_icon,
            "benefit_3_title": config.benefit_3_title,
            "benefit_3_subtext": config.benefit_3_subtext,
            "benefit_3_icon": config.benefit_3_icon,
            "benefit_4_title": config.benefit_4_title,
            "benefit_4_subtext": config.benefit_4_subtext,
            "benefit_4_icon": config.benefit_4_icon,
            "support_email": config.support_email,
            "support_phone": config.support_phone,
            "show_newsletter": config.show_newsletter,
            "newsletter_title": config.newsletter_title,
            "newsletter_body": config.newsletter_body,

            # ── Navigation ────────────────────────────────────────────────
            "nav_links": config.nav_links(),

            # ── Footer ────────────────────────────────────────────────────
            "footer_tagline": config.footer_tagline,
            "footer_col2_heading": config.footer_col2_heading,
            "footer_col2_links": config.footer_col2_link_list(),
            "footer_col3_heading": config.footer_col3_heading,
            "footer_col3_links": config.footer_col3_link_list(),
            "footer_col4_heading": config.footer_col4_heading,
            "footer_col4_links": config.footer_col4_link_list(),
        }
    except Exception:
        # Fallback if DB is not ready during migrations
        return {
            "shop_name": "My Shop",
            "logo_text": "My Shop",
            "theme_css_path": "themes/default/theme.css",
            "theme_template": "default",
            "theme_base_template": "themes/default/base.html",
            "hero_slides": [],
            "promo_badge": "Limited Time Offer",
            "promo_title": "Premium Collection is 30% Off",
            "promo_body": "Upgrade your lifestyle with our exclusive collection.",
            "promo_button_label": "Claim Discount",
            "promo_image": None,
            "show_benefits": True,
            "show_newsletter": True,
            "newsletter_title": "Join our Newsletter",
            "newsletter_body": "Subscribe to get special offers and once-in-a-lifetime deals.",
            "nav_links": [],
            "footer_tagline": "Quality products delivered to your doorstep.",
            "footer_col2_heading": "Shop",
            "footer_col2_links": [("All Products", "/"), ("My Cart", "/cart/")],
            "footer_col3_heading": "Company",
            "footer_col3_links": [("About Us", "#"), ("Sustainability", "#"), ("Careers", "#")],
            "footer_col4_heading": "Support",
            "footer_col4_links": [("Help Center", "#"), ("Privacy Policy", "#"), ("Terms of Use", "#")],
        }
