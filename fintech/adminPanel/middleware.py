# adminPanel/middleware.py
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from users.models import User


class AdminPanelMiddleware:
    """
    Middleware that protects all /api/admin/ routes.
    Accepts both JWT tokens and session authentication.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/admin/'):

            # Check session auth first (browser login)
            if request.user.is_authenticated:
                if request.user.user_type not in ('admin', 'super_admin'):
                    return JsonResponse(
                        {'error': 'Admin access required.'},
                        status=403
                    )
                return self.get_response(request)

            # Fall back to JWT token auth
            user = self.get_user_from_token(request)

            if user is None:
                return JsonResponse(
                    {'error': 'Authentication required.'},
                    status=401
                )

            if user.user_type != 'admin':
                return JsonResponse(
                    {'error': 'Admin access required.'},
                    status=403
                )

        return self.get_response(request)

    def get_user_from_token(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None

        token_str = auth_header.split(' ')[1]

        try:
            token = AccessToken(token_str)
            user_id = token['user_id']
            return User.objects.get(id=user_id)
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None