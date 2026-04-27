import secrets
from django.db import models



class HeroSlide(models.Model):
    shop_config = models.ForeignKey("ShopConfig", related_name="slides", on_delete=models.CASCADE)
    tagline = models.CharField(max_length=200, blank=True)
    highlight = models.CharField(max_length=200, blank=True)
    subtext = models.CharField(max_length=500, blank=True)
    button_label = models.CharField(max_length=80, blank=True)
    button_url = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="storefront/hero/", null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Slide: {self.tagline} {self.highlight}"


class ShopConfig(models.Model):
    """
    Singleton model — only one row should ever exist.
    Stores shop-wide settings including the API key for
    the Flutter desktop app to use when syncing.
    """

    # ── Core ──────────────────────────────────────────────────────────────────
    shop_name = models.CharField(max_length=200, default="My Shop")
    logo_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="Text displayed as the logo in the nav bar. Leave blank to use the shop name.",
    )
    logo = models.ImageField(
        upload_to="shop/",
        blank=True,
        null=True,
        help_text="Upload a logo image. If provided, this will be used instead of logo text.",
    )
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
            ("aurora", "Aurora Theme"),
            ("squareshoppe", "SquareShoppe Theme"),
        ],
        default="default",
        help_text="Select the visual theme for the storefront.",
    )
    show_top_bar = models.BooleanField(
        default=True,
        help_text="Show a thin informational bar above the main navigation.",
    )
    top_bar_offer = models.CharField(
        max_length=200,
        default="Free Shipping on all orders over ₹1,000!",
        help_text="Special announcement or offer text for the top bar.",
    )
    store_address = models.CharField(
        max_length=500,
        default="123 Luxury Street, Fashion District",
        help_text="Physical address shown in the top bar.",
    )

    # ── Homepage — Promo Banner ────────────────────────────────────────────────
    show_promo_banner = models.BooleanField(
        default=True,
        help_text="Show or hide the promotional banner section on the homepage.",
    )
    promo_badge = models.CharField(
        max_length=80,
        default="Limited Time Offer",
        help_text="Small uppercase badge label above the promo heading.",
    )
    promo_title = models.CharField(
        max_length=200,
        default="Premium Collection is 30% Off",
        help_text="Main heading inside the promo banner.",
    )
    promo_body = models.CharField(
        max_length=500,
        default="Upgrade your lifestyle with our exclusive collection. Use code LUXE30 at checkout.",
        help_text="Body text inside the promo banner.",
    )
    promo_button_label = models.CharField(
        max_length=80,
        default="Claim Discount",
        help_text="CTA button label inside the promo banner.",
    )
    promo_button_url = models.CharField(
        max_length=200,
        default="/",
        help_text="URL for the promo banner button.",
    )
    promo_image = models.ImageField(
        upload_to="storefront/",
        null=True,
        blank=True,
        help_text="Right-side image for the promo banner. Leave blank for the default.",
    )

    # ── Homepage — Extra Toggles ──────────────────────────────────────────────
    show_benefits = models.BooleanField(
        default=True,
        help_text="Show the Free Shipping / Easy Returns / Secure Payment / 24/7 Support grid.",
    )
    show_sidebar_promo = models.BooleanField(
        default=True,
        help_text="Show the promotional box in the product list sidebar.",
    )
    sidebar_promo_title = models.CharField(
        max_length=100,
        default="Free Delivery",
        help_text="Heading for the sidebar promo box.",
    )
    sidebar_promo_body = models.CharField(
        max_length=200,
        default="On all orders above ₹1,000.",
        help_text="Subtext for the sidebar promo box.",
    )
    sidebar_promo_icon = models.CharField(
        max_length=50,
        default="fas fa-shipping-fast",
        help_text="FontAwesome icon class.",
    )
    benefit_1_title = models.CharField(max_length=100, default="Free Shipping")
    benefit_1_subtext = models.CharField(max_length=200, default="On all orders over ₹1,000.")
    benefit_1_icon = models.CharField(max_length=50, default="fas fa-truck", help_text="FontAwesome icon class.")
    
    benefit_2_title = models.CharField(max_length=100, default="Easy Returns")
    benefit_2_subtext = models.CharField(max_length=200, default="30 days free return policy.")
    benefit_2_icon = models.CharField(max_length=50, default="fas fa-undo")
    
    benefit_3_title = models.CharField(max_length=100, default="Secure Payment")
    benefit_3_subtext = models.CharField(max_length=200, default="Protected by top-notch security.")
    benefit_3_icon = models.CharField(max_length=50, default="fas fa-shield-alt")
    
    benefit_4_title = models.CharField(max_length=100, default="24/7 Support")
    benefit_4_subtext = models.CharField(max_length=200, default="Our team is always here for you.")
    benefit_4_icon = models.CharField(max_length=50, default="fas fa-headset")

    support_email = models.EmailField(default="support@example.com")
    support_phone = models.CharField(max_length=20, default="+91 99999 99999")

    show_newsletter = models.BooleanField(
        default=True,
        help_text="Show the newsletter sign-up box on the homepage.",
    )
    newsletter_title = models.CharField(
        max_length=200,
        default="Join our Newsletter",
        help_text="Heading for the newsletter subscription box.",
    )
    newsletter_body = models.CharField(
        max_length=500,
        default="Subscribe to get special offers, free giveaways, and once-in-a-lifetime deals.",
        help_text="Body text inside the newsletter box.",
    )

    # ── Navigation Links (up to 4 custom slots) ───────────────────────────────
    nav_link_1_label = models.CharField(max_length=80, blank=True, help_text="Label for nav link 1 (leave blank to hide).")
    nav_link_1_url = models.CharField(max_length=200, blank=True, default="/", help_text="URL for nav link 1.")
    nav_link_2_label = models.CharField(max_length=80, blank=True, help_text="Label for nav link 2 (leave blank to hide).")
    nav_link_2_url = models.CharField(max_length=200, blank=True, default="/", help_text="URL for nav link 2.")
    nav_link_3_label = models.CharField(max_length=80, blank=True, help_text="Label for nav link 3 (leave blank to hide).")
    nav_link_3_url = models.CharField(max_length=200, blank=True, default="/", help_text="URL for nav link 3.")
    nav_link_4_label = models.CharField(max_length=80, blank=True, help_text="Label for nav link 4 (leave blank to hide).")
    nav_link_4_url = models.CharField(max_length=200, blank=True, default="/", help_text="URL for nav link 4.")

    # ── Footer ─────────────────────────────────────────────────────────────────
    footer_tagline = models.CharField(
        max_length=500,
        default="Quality products delivered to your doorstep. Experience the best of online shopping with us.",
        help_text="Short description shown below the logo in the footer.",
    )
    # Column 2
    footer_col2_heading = models.CharField(max_length=80, default="Shop", help_text="Heading for footer column 2.")
    footer_col2_link_1_label = models.CharField(max_length=80, blank=True)
    footer_col2_link_1_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col2_link_2_label = models.CharField(max_length=80, blank=True)
    footer_col2_link_2_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col2_link_3_label = models.CharField(max_length=80, blank=True)
    footer_col2_link_3_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col2_link_4_label = models.CharField(max_length=80, blank=True)
    footer_col2_link_4_url = models.CharField(max_length=200, blank=True, default="/")

    # Column 3
    footer_col3_heading = models.CharField(max_length=80, default="Company", help_text="Heading for footer column 3.")
    footer_col3_link_1_label = models.CharField(max_length=80, blank=True)
    footer_col3_link_1_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col3_link_2_label = models.CharField(max_length=80, blank=True)
    footer_col3_link_2_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col3_link_3_label = models.CharField(max_length=80, blank=True)
    footer_col3_link_3_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col3_link_4_label = models.CharField(max_length=80, blank=True)
    footer_col3_link_4_url = models.CharField(max_length=200, blank=True, default="/")

    # Column 4
    footer_col4_heading = models.CharField(max_length=80, default="Support", help_text="Heading for footer column 4.")
    footer_col4_link_1_label = models.CharField(max_length=80, blank=True)
    footer_col4_link_1_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col4_link_2_label = models.CharField(max_length=80, blank=True)
    footer_col4_link_2_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col4_link_3_label = models.CharField(max_length=80, blank=True)
    footer_col4_link_3_url = models.CharField(max_length=200, blank=True, default="/")
    footer_col4_link_4_label = models.CharField(max_length=80, blank=True)
    footer_col4_link_4_url = models.CharField(max_length=200, blank=True, default="/")

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

    def nav_links(self):
        """Return a list of (label, url) tuples for non-empty nav link slots."""
        slots = [
            (self.nav_link_1_label, self.nav_link_1_url),
            (self.nav_link_2_label, self.nav_link_2_url),
            (self.nav_link_3_label, self.nav_link_3_url),
            (self.nav_link_4_label, self.nav_link_4_url),
        ]
        return [(label, url) for label, url in slots if label.strip()]

    def footer_col2_link_list(self):
        links = [
            (self.footer_col2_link_1_label, self.footer_col2_link_1_url),
            (self.footer_col2_link_2_label, self.footer_col2_link_2_url),
            (self.footer_col2_link_3_label, self.footer_col2_link_3_url),
            (self.footer_col2_link_4_label, self.footer_col2_link_4_url),
        ]
        return [(label, url) for label, url in links if label.strip()]

    def footer_col3_link_list(self):
        links = [
            (self.footer_col3_link_1_label, self.footer_col3_link_1_url),
            (self.footer_col3_link_2_label, self.footer_col3_link_2_url),
            (self.footer_col3_link_3_label, self.footer_col3_link_3_url),
            (self.footer_col3_link_4_label, self.footer_col3_link_4_url),
        ]
        return [(label, url) for label, url in links if label.strip()]

    def footer_col4_link_list(self):
        links = [
            (self.footer_col4_link_1_label, self.footer_col4_link_1_url),
            (self.footer_col4_link_2_label, self.footer_col4_link_2_url),
            (self.footer_col4_link_3_label, self.footer_col4_link_3_url),
            (self.footer_col4_link_4_label, self.footer_col4_link_4_url),
        ]
        return [(label, url) for label, url in links if label.strip()]
