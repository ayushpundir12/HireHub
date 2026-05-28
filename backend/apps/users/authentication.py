from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from jose import jwt, JWTError
from django.conf import settings
import requests

_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        try:
            url = f"https://{settings.SUPABASE_PROJECT_REF}.supabase.co/auth/v1/.well-known/jwks.json"
            response = requests.get(url, timeout=10)
            _jwks_cache = response.json()
            print(f"DEBUG JWKS: {_jwks_cache}")
        except Exception as e:
            raise AuthenticationFailed(f'Could not fetch JWKS: {str(e)}')
    return _jwks_cache

class SupabaseJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            unverified_header = jwt.get_unverified_header(token)
            algorithm = unverified_header.get('alg', 'ES256')

            if algorithm == 'HS256':
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=['HS256'],
                    audience='authenticated'
                )
            else:
                payload = jwt.decode(
                    token,
                    get_jwks(),
                    algorithms=['ES256', 'RS256'],
                    audience='authenticated'
                )

        except JWTError as e:
            raise AuthenticationFailed(f'Invalid or expired token: {str(e)}')
        except Exception as e:
            raise AuthenticationFailed('Authentication provider is currently unavailable.')

        from apps.users.models import User
        try:
            user = User.objects.get(id=payload['sub'])
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')

        return (user, token)