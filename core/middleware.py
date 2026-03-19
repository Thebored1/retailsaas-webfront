from django.contrib import messages
from django.shortcuts import redirect, render
from core.models import ShopConfig


DELIVERY_GROUP_NAME = "delivery_agents"


class DeliveryAgentAccessMiddleware:
    """
    Prevent delivery agent accounts from accessing the storefront.
    Allow only /delivery/, /admin/, /api/ and static/media assets.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        path = request.path or ""

        if user and user.is_authenticated:
            is_delivery_agent = user.is_superuser or user.groups.filter(
                name=DELIVERY_GROUP_NAME
            ).exists()

            if is_delivery_agent:
                allowed_prefixes = (
                    "/delivery/",
                    "/api/",
                    "/static/",
                    "/media/",
                )

                if not path.startswith(allowed_prefixes):
                    try:
                        theme = ShopConfig.get().shop_template or "default"
                    except Exception:
                        theme = "default"
                    template = f"themes/{theme}/delivery/denied.html"
                    messages.error(
                        request,
                        "Delivery agent accounts can only access the delivery console.",
                    )
                    return render(request, template, status=403)

        return self.get_response(request)
