from django.utils.deprecation import MiddlewareMixin
from .utils.jwt import decode_token
from .utils.django_user_proxy import AuthenticatedUser, AnonymousUser

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload:
                request.user = AuthenticatedUser(payload)
            else:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()
