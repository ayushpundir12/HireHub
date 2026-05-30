from celery import shared_task
from django.conf import settings
from twilio.rest import Client
import random
import string


def generate_otp(length=6) -> str:
    return ''.join(random.choices(string.digits, k=length))


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_completion_otp(self, booking_id: str, client_phone: str, otp: str):
    """
    Sends the completion OTP to the client's phone via Twilio.
    Called by the pro when they request job completion.

    Why Celery for an SMS?
    The view returns immediately — the SMS is delivered asynchronously.
    If Twilio is slow or fails, Celery retries automatically (max 3 times).
    The user experience isn't blocked waiting for the SMS API.
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=(
                f"Your HireHub job completion code is: {otp}\n"
                f"Share this with your service pro to confirm the job is done.\n"
                f"Valid for 10 minutes."
            ),
            from_=settings.TWILIO_PHONE_NUMBER,
            to=client_phone,
        )
    except Exception as exc:
        raise self.retry(exc=exc)