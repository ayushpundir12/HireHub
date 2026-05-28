"""
Auth views for HireHub.

Endpoints:
    POST /api/v1/auth/signup/        → Create Supabase user + Django profile
    POST /api/v1/auth/verify-email/  → Verify email with 6-digit OTP
    POST /api/v1/auth/login/         → Authenticate via Supabase, return tokens
    GET  /api/v1/auth/me/            → Get the current user's profile
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.core.cache import cache
from django.conf import settings
from supabase import create_client

from .models import User
from .serializers import (
    UserSerializer,
    SignupSerializer,
    VerifySerializer,
)
from .tasks import send_verification_email, send_phone_otp

import logging

from .permissions import IsFullyVerified, IsEmailVerified

logger = logging.getLogger(__name__)

# ── Supabase admin client (uses service role key) ──
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


# ──────────────────────────────────────────────
#  POST /api/v1/auth/signup/
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """
    Register a new user.

    1. Validate input
    2. Create the user in Supabase Auth
    3. Create a matching Django profile
    4. Fire off an email verification OTP (async via Celery)
    """
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    
    try:
        # Create user in Supabase Auth
        sb_response = supabase.auth.admin.create_user({
            'email': data['email'],
            'password': data['password'],
            'email_confirm': True,  # Auto-confirm in Supabase; we handle actual verification via OTP
        })

        sb_user = sb_response.user

        try:
            user = User.objects.create(
                id=sb_user.id,
                email=data['email'],
                full_name=data['full_name'],
                phone_number=data['phone_number'],
            )
        except Exception as django_error:
            supabase.auth.admin.delete_user(sb_user.id)
            raise django_error

        sign_in = supabase.auth.sign_in_with_password({
            'email': data['email'],
            'password': data['password']
        })

        # Send verification OTPs asynchronously (email + phone)
        send_verification_email.delay(str(user.id), user.email)
        send_phone_otp.delay(str(user.id), data['phone_number'])

        return Response({
            'message': 'Account created. Check your email and phone for verification codes.',
            'user_id': str(user.id),
            'access_token': sign_in.session.access_token,
            'next_step': 'verify'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Signup failed for {data['email']}: {e}")
        return Response(
            {'error': 'Signup failed. Please try again.', 'detail': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def oauth_callback(request):
    """
    Called after Supabase OAuth completes.
    Frontend sends the access_token it got from Supabase.
    We create/update the user record in Django.
    """
    access_token=request.data.get('access_token')

    if not access_token:
        return Response(
            {'error':
            'Access token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate the token with Supabase
        sb_response = supabase.auth.get_user(access_token)
        sb_user = sb_response.user

        if not sb_user:
            return Response(
                {'error': 'Invalid access token'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Get or create the Django user
        user, created = User.objects.get_or_create(
            id=sb_user.id,
            defaults={
                'email': sb_user.email,
                'full_name': sb_user.user_metadata.get('full_name', ''),
                'role': sb_user.user_metadata.get('role', 'client'),
                'phone_number': sb_user.user_metadata.get('phone_number', ''),
            }
        )

        # If user already exists, update any missing fields
        if created:

            return Response({
                'message':'Account via OAuth created successfully',
                'user_id':str(user.id),
                'is_new':True,
                'next_step':'verify_phone',
                'acess_token':access_token,                
            },status=status.HTTP_201_CREATED)

        else:
            # Returning OAuth user
            if not user.is_number_verified:
                return Response({
                    'message':    'Please verify your phone number.',
                    'is_new':     False,
                    'next_step':  'verify_phone',
                    'access_token': access_token,
                })

            return Response({
                'message':      'Login successful.',
                'is_new':       False,
                'next_step':    'home',
                'access_token': access_token,
                'user':         UserSerializer(user).data,
            })
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        return Response(
            {'error': 'Failed to process OAuth callback. Please try again.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ──────────────────────────────────────────────
#  POST /api/v1/auth/verify-email/
# ──────────────────────────────────────────────

# apps/users/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify(request):
    "single end point to verify eamil and phone number"
    email_otp=request.data.get('email_otp')
    phone_otp=request.data.get('phone_otp')

    if not email_otp or not phone_otp:
        return Response(
            {'error':'Please provide both email and phone OTPs'},
            status= status.HTTP_400_BAD_REQUEST
        
        )

    user_id=request.user.id
    email_otp_cached=cache.get(f"otp:email:{user_id}")
    phone_otp_cached=cache.get(f"phone_otp:{user_id}")

    errors={}

    if not email_otp_cached:
        errors['email_otp']='OTP has expired. Please request a new one.'
    elif email_otp != email_otp_cached:
        errors['email_otp']='Invalid OTP. Please try again.'
    
    if not phone_otp_cached:
        errors['phone_otp']='OTP has expired. Please request a new one.'
    elif phone_otp != phone_otp_cached:
        errors['phone_otp']='Invalid OTP. Please try again.'
    
    if errors:
        return Response(errors,status=status.HTTP_400_BAD_REQUEST)

    request.user.is_email_verified = True
    request.user.is_number_verified = True
    request.user.save(update_fields=['is_email_verified', 'is_number_verified'])

    cache.delete(f"otp:email:{user_id}")
    cache.delete(f"phone_otp:{user_id}")
    
    return Response({'message':'Email and phone number verified successfully.'})
        


    
# ──────────────────────────────────────────────
#  POST /api/v1/auth/login/
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate via Supabase and return access + refresh tokens.
    The frontend stores these tokens and sends the access token
    as `Authorization: Bearer <token>` on subsequent requests.
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {'error': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Authenticate against Supabase Auth
        sb_response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password,
        })

        # Also fetch the user's profile from our database
        user = User.objects.get(id=sb_response.user.id)

        return Response({
            'access_token': sb_response.session.access_token,
            'refresh_token': sb_response.session.refresh_token,
            'expires_in': sb_response.session.expires_in,
            'user': UserSerializer(user).data,
        })

    except User.DoesNotExist:
        return Response(
            {'error': 'User profile not found. Please sign up first.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(f"Login failed for {email}: {e}")
        return Response(
            {'error': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )




# ──────────────────────────────────────────────
#  GET /api/v1/auth/me/
# ──────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsFullyVerified])
def me(request):
    """Return the authenticated user's profile."""
    return Response(UserSerializer(request.user).data)


# ──────────────────────────────────────────────
#  POST /api/v1/auth/verify-account/
#  Verify BOTH email and phone OTP on the same page
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_account(request):
    """
    Verify both email and phone in a single request.

    Expects:
        {
            "email_otp": "123456",
            "phone_otp": "654321"
        }

    Either field can be omitted if that channel is already verified.
    """
    user = request.user
    email_otp = request.data.get('email_otp')
    phone_otp = request.data.get('phone_otp')
    errors = {}
    updated_fields = []

    # ── Email verification ──
    if email_otp:
        if user.is_email_verified:
            pass  # already verified, skip
        else:
            cached = cache.get(f"otp:email:{user.id}")
            if cached is None:
                errors['email_otp'] = 'OTP has expired. Please request a new one.'
            elif email_otp != cached:
                errors['email_otp'] = 'Invalid email OTP.'
            else:
                user.is_email_verified = True
                updated_fields.append('is_email_verified')
                cache.delete(f"otp:email:{user.id}")

    # ── Phone verification ──
    if phone_otp:
        if user.is_number_verified:
            pass  # already verified, skip
        else:
            cached = cache.get(f"phone_otp:{user.id}")
            if cached is None:
                errors['phone_otp'] = 'OTP has expired. Please request a new one.'
            elif phone_otp != cached:
                errors['phone_otp'] = 'Invalid phone OTP.'
            else:
                user.is_number_verified = True
                updated_fields.append('is_number_verified')
                cache.delete(f"phone_otp:{user.id}")

    # Return errors if any OTP failed
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    if not email_otp and not phone_otp:
        return Response(
            {'error': 'Provide at least one of email_otp or phone_otp.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Persist changes
    if updated_fields:
        updated_fields.append('updated_at')
        user.save(update_fields=updated_fields)

    return Response({
        'message': 'Verification successful.',
        'is_email_verified': user.is_email_verified,
        'is_number_verified': user.is_number_verified,
    })


# ──────────────────────────────────────────────
#  POST /api/v1/auth/resend-otp/
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_otp(request):
    """
    Resend OTP for email, phone, or both.

    Expects:
        { "type": "email" | "phone" | "both" }
    """
    user = request.user
    otp_type = request.data.get('type', 'both')

    if otp_type in ('email', 'both') and not user.is_email_verified:
        send_verification_email.delay(str(user.id), user.email)

    if otp_type in ('phone', 'both') and not user.is_number_verified:
        if user.phone_number:
            send_phone_otp.delay(str(user.id), user.phone_number)
        else:
            return Response(
                {'error': 'No phone number on file. Update your profile first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response({'message': f'OTP(s) resent for: {otp_type}.'})


# apps/users/views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_phone_only(request):
    """
    For OAuth users who only need phone verification
    Email is already verified by Google/Facebook
    """
    phone_number = request.data.get('phone_number')
    phone_otp    = request.data.get('phone_otp')

    # Step 1 — if no OTP yet, send it first
    if not phone_otp:
        if not phone_number:
            return Response(
                {'error': 'Phone number required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.phone_number = phone_number
        request.user.save(update_fields=['phone_number'])

        send_phone_otp.delay(str(request.user.id), phone_number)

        return Response({
            'message': 'OTP sent to your phone number.'
        })

    # Step 2 — verify OTP
    user_id    = str(request.user.id)
    cached_otp = cache.get(f"otp:phone:{user_id}")

    if not cached_otp:
        return Response(
            {'error': 'OTP expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if cached_otp != phone_otp:
        return Response(
            {'error': 'Invalid OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    request.user.is_number_verified = True
    request.user.save(update_fields=['is_number_verified'])
    cache.delete(f"otp:phone:{user_id}")

    return Response({
        'message': 'Phone verified. You can now access the platform.',
        'user':    UserSerializer(request.user).data
    })

@api_view(['POST'])
@permission_classes([IsFullyVerified])
def logout(request):
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1]
        supabase.auth.admin.sign_out(token)
    except Exception:
        pass  # even if Supabase fails, we treat as logged out

    return Response({'message': 'Logged out successfully.'})