import hashlib
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class APIKeyUser:
    is_authenticated = True


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw_key = request.headers.get("X-API-Key")
        if not raw_key:
            return None

        from core.models import ShopConfig
        config = ShopConfig.get()
        if not config.api_key or raw_key != config.api_key:
            raise AuthenticationFailed("Invalid API key")

        return (APIKeyUser(), None)

    def authenticate_header(self, request):
        return "X-API-Key"
