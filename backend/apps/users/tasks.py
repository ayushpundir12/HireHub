from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
import random
import string
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)


def generate_otp(length=6):
    """Generate a random numeric OTP string."""
    return ''.join(random.choices(string.digits, k=length))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email(self, user_id: str, email: str):
    """
    Generate an OTP, store it in Redis, and email it to the user.

    Args:
        user_id: UUID string — used as the Redis key for OTP lookup.
        email: The recipient's email address.
    """
    otp = generate_otp()

    # Store OTP in Redis — expires in 10 minutes
    cache.set(f"otp:email:{user_id}", otp, timeout=600)

    try:
        send_mail(
            subject='Your HireHub verification code',
            message=f'Your verification code is: {otp}\n\nExpires in 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {email}")
    except Exception as exc:
        logger.error(f"Failed to send verification email to {email}: {exc}")
        raise self.retry(exc=exc)



@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_phone_otp(self, user_id: str, phone_number: str):
    otp = generate_otp()
    
    # Store in Redis — 10 min expiry
    cache.set(f"phone_otp:{user_id}", otp, timeout=600)
    
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        client.messages.create(
            body=f"Your HireHub verification code is: {otp}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number  # must include country code e.g. +971501234567
        )
    except Exception as exc:
        raise self.retry(exc=exc)